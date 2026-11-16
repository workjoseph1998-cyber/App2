"""AssetPass routes; shares authentication, authorization and database with Pulse."""

import secrets
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

from flask import abort, flash, g, redirect, render_template, request, send_file, url_for

from . import (
    ASSET_CATEGORIES,
    ASSET_STATUSES,
    asset_or_404,
    audit,
    can_asset,
    choice,
    date_value,
    db,
    manager,
    notify,
    now,
    one,
    protected,
    required,
    rows,
)


def register_assets(app):
    def filtered_assets():
        result = []
        for a in rows("SELECT * FROM assets ORDER BY asset_tag"):
            if not can_asset(a):
                continue
            if (
                request.args.get("q", "").lower()
                not in (
                    " ".join(
                        str(a[k] or "") for k in ("asset_tag", "model", "serial", "manufacturer")
                    )
                ).lower()
            ):
                continue
            if any(request.args.get(k) and request.args[k] != a[k] for k in ("status", "category")):
                continue
            if request.args.get("department") and not one(
                "SELECT 1 FROM assignments x JOIN users u ON u.id=x.user_id WHERE x.asset_id=? AND x.returned_at IS NULL AND u.department_id=?",
                (a["id"], request.args["department"]),
            ):
                continue
            w = request.args.get("warranty")
            expiry = a["warranty_expiration"]
            today = datetime.now(timezone.utc).date()
            soon = (today + timedelta(days=30)).isoformat()
            if w == "expiring" and not (expiry and today.isoformat() <= expiry <= soon):
                continue
            if w == "expired" and not (expiry and expiry < today.isoformat()):
                continue
            result.append(a)
        return result

    @app.get("/assetpass")
    @protected()
    def asset_overview():
        assets = filtered_assets()
        ids = {a["id"] for a in assets}
        xs = [
            x
            for x in rows("SELECT * FROM assignments WHERE returned_at IS NULL")
            if x["asset_id"] in ids
        ]
        today = datetime.now(timezone.utc).date()
        metrics = {
            "Total assets": len(assets),
            **{s: sum(a["status"] == s for a in assets) for s in ASSET_STATUSES},
            "Pending handovers": sum(not x["confirmed_at"] for x in xs),
            "Pending returns": sum(bool(x["return_requested_at"]) for x in xs),
            "Expiring warranties": sum(
                bool(
                    a["warranty_expiration"]
                    and today.isoformat()
                    <= a["warranty_expiration"]
                    <= (today + timedelta(days=30)).isoformat()
                )
                for a in assets
            ),
        }
        return render_template("asset_overview.html", metrics=metrics, assets=assets[:8])

    @app.get("/assetpass/inventory")
    @protected()
    def inventory():
        return render_template("inventory.html", assets=filtered_assets(), mine=False)

    @app.get("/assetpass/mine")
    @protected()
    def my_equipment():
        assets = rows(
            "SELECT a.* FROM assets a JOIN assignments x ON x.asset_id=a.id WHERE x.user_id=? AND x.returned_at IS NULL",
            (g.user["id"],),
        )
        history = rows(
            "SELECT x.*,a.asset_tag FROM assignments x JOIN assets a ON a.id=x.asset_id WHERE x.user_id=? ORDER BY x.id DESC",
            (g.user["id"],),
        )
        return render_template("inventory.html", assets=assets, mine=True, history=history)

    @app.route("/assetpass/new", methods=["GET", "POST"])
    @protected("admin", "asset_manager")
    def new_asset():
        if request.method == "POST":
            tag = required("asset_tag")
            cost = request.form.get("purchase_cost", "").strip()
            if cost:
                from decimal import Decimal, InvalidOperation

                try:
                    c = Decimal(cost)
                    if not c.is_finite() or c < 0:
                        raise ValueError("Invalid cost.")
                    cost = str(c.quantize(Decimal(".01")))
                except InvalidOperation:
                    raise ValueError("Invalid cost.")
            with db():
                aid = (
                    db()
                    .execute(
                        "INSERT INTO assets(asset_tag,category,manufacturer,model,serial,description,purchase_date,purchase_cost,supplier,warranty_expiration,condition,status,location,notes) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                        (
                            tag,
                            choice("category", ASSET_CATEGORIES),
                            request.form.get("manufacturer"),
                            request.form.get("model"),
                            request.form.get("serial", "").strip() or None,
                            request.form.get("description"),
                            date_value("purchase_date"),
                            cost,
                            request.form.get("supplier"),
                            date_value("warranty_expiration"),
                            required("condition"),
                            "Available",
                            request.form.get("location"),
                            request.form.get("notes"),
                        ),
                    )
                    .lastrowid
                )
                audit(aid, "Registered", tag)
            return redirect(url_for("asset_detail", aid=aid))
        return render_template("asset_form.html")

    @app.route("/assetpass/assets/<int:aid>", methods=["GET", "POST"])
    @protected()
    def asset_detail(aid):
        a = asset_or_404(aid)
        if request.method == "POST":
            if not manager():
                abort(403)
            status = choice("status", ASSET_STATUSES)
            with db():
                db().execute("BEGIN IMMEDIATE")
                active = one(
                    "SELECT * FROM assignments WHERE asset_id=? AND returned_at IS NULL", (aid,)
                )
                if status == "Assigned" and not active:
                    raise ValueError("Use the assignment workflow.")
                if active and status not in ("Assigned", "Under Repair", "Missing"):
                    raise ValueError(
                        "Verify and close the active return before releasing this asset."
                    )
                if a["status"] == "Retired" and status != "Retired":
                    raise ValueError("Retired assets cannot be reactivated.")
                db().execute(
                    "UPDATE assets SET status=?,condition=?,location=?,notes=?,retirement_date=?,disposal_status=? WHERE id=?",
                    (
                        status,
                        required("condition"),
                        request.form.get("location"),
                        request.form.get("notes"),
                        datetime.now(timezone.utc).date().isoformat()
                        if status == "Retired"
                        else a["retirement_date"],
                        request.form.get("disposal_status"),
                        aid,
                    ),
                )
                audit(aid, "Inventory updated", status + " · " + request.form.get("notes", ""))
            return redirect(request.path)
        active = one(
            "SELECT x.*,u.name employee FROM assignments x JOIN users u ON u.id=x.user_id WHERE x.asset_id=? AND x.returned_at IS NULL",
            (aid,),
        )
        hist = (
            rows(
                "SELECT x.*,u.name employee FROM assignments x JOIN users u ON u.id=x.user_id WHERE x.asset_id=? ORDER BY x.id DESC",
                (aid,),
            )
            if manager()
            else rows(
                "SELECT x.*,u.name employee FROM assignments x JOIN users u ON u.id=x.user_id WHERE x.asset_id=? AND x.user_id=? ORDER BY x.id DESC",
                (aid, g.user["id"]),
            )
        )
        if g.user["role"] == "department_manager" and g.user["department_id"]:
            hist = rows(
                "SELECT x.*,u.name employee FROM assignments x JOIN users u ON u.id=x.user_id WHERE x.asset_id=? AND u.department_id=? ORDER BY x.id DESC",
                (aid, g.user["department_id"]),
            )
        return render_template(
            "asset_detail.html",
            a=a,
            active=active,
            history=hist,
            attachments=[
                f
                for f in rows("SELECT * FROM attachments WHERE asset_id=?", (aid,))
                if manager()
                or not f["issue_id"]
                or one(
                    "SELECT 1 FROM issues WHERE id=? AND user_id=?", (f["issue_id"], g.user["id"])
                )
            ],
            employees=rows("SELECT id,name FROM users WHERE enabled=1 ORDER BY name")
            if manager()
            else [],
            events=rows(
                "SELECT a.*,u.name actor FROM audit a LEFT JOIN users u ON u.id=a.actor_id WHERE asset_id=? ORDER BY id DESC",
                (aid,),
            )
            if manager()
            else [],
        )

    @app.route("/assetpass/assets/<int:aid>/edit", methods=["GET", "POST"])
    @protected("admin", "asset_manager")
    def edit_asset(aid):
        a = asset_or_404(aid)
        if request.method == "POST":
            from decimal import Decimal, InvalidOperation

            cost = request.form.get("purchase_cost", "").strip()
            if cost:
                try:
                    amount = Decimal(cost)
                    if not amount.is_finite() or amount < 0:
                        raise ValueError("Invalid purchase cost.")
                    cost = str(amount.quantize(Decimal(".01")))
                except InvalidOperation:
                    raise ValueError("Invalid purchase cost.")
            with db():
                db().execute(
                    "UPDATE assets SET asset_tag=?,category=?,manufacturer=?,model=?,serial=?,description=?,purchase_date=?,purchase_cost=?,supplier=?,warranty_expiration=?,location=?,notes=? WHERE id=?",
                    (
                        required("asset_tag"),
                        choice("category", ASSET_CATEGORIES),
                        request.form.get("manufacturer"),
                        request.form.get("model"),
                        request.form.get("serial", "").strip() or None,
                        request.form.get("description"),
                        date_value("purchase_date"),
                        cost,
                        request.form.get("supplier"),
                        date_value("warranty_expiration"),
                        request.form.get("location"),
                        request.form.get("notes"),
                        aid,
                    ),
                )
                audit(aid, "Specifications updated")
            return redirect(url_for("asset_detail", aid=aid))
        return render_template("asset_edit.html", a=a)

    @app.post("/assetpass/assets/<int:aid>/assign")
    @protected("admin", "asset_manager")
    def assign(aid):
        with db():
            db().execute("BEGIN IMMEDIATE")
            a = one("SELECT * FROM assets WHERE id=?", (aid,))
            if not a:
                abort(404)
            if a["status"] != "Available":
                raise ValueError("Only available equipment can be assigned.")
            assigned = date_value("assigned_at") or datetime.now(timezone.utc).date().isoformat()
            if assigned > datetime.now(timezone.utc).date().isoformat():
                raise ValueError("Assignment date cannot be in the future.")
            uid = int(required("user_id"))
            if not one("SELECT 1 FROM users WHERE id=? AND enabled=1", (uid,)):
                raise ValueError("Select an enabled employee.")
            db().execute(
                "INSERT INTO assignments(asset_id,user_id,assigned_at,condition_out,notes,created_by) VALUES(?,?,?,?,?,?)",
                (
                    aid,
                    uid,
                    assigned,
                    required("condition"),
                    request.form.get("notes"),
                    g.user["id"],
                ),
            )
            db().execute("UPDATE assets SET status='Assigned' WHERE id=?", (aid,))
            audit(aid, "Assigned", f"Employee #{uid}")
            notify(uid, "Confirm receipt of " + a["asset_tag"], f"/assetpass/assets/{aid}")
        return redirect(url_for("asset_detail", aid=aid))

    @app.post("/assetpass/assignments/<int:xid>/<action>")
    @protected()
    def assignment_action(xid, action):
        with db():
            db().execute("BEGIN IMMEDIATE")
            x = one("SELECT * FROM assignments WHERE id=?", (xid,))
            if not x:
                abort(404)
            if x["returned_at"]:
                raise ValueError("This assignment is closed.")
            if action in ("confirm", "request-return"):
                if x["user_id"] != g.user["id"]:
                    abort(403)
                if action == "confirm":
                    if x["confirmed_at"]:
                        raise ValueError("Receipt already confirmed.")
                    db().execute(
                        "UPDATE assignments SET confirmed_at=?,confirmed_by=? WHERE id=?",
                        (now(), g.user["id"], xid),
                    )
                else:
                    if x["return_requested_at"]:
                        raise ValueError("Return already requested.")
                    db().execute(
                        "UPDATE assignments SET return_requested_at=? WHERE id=?", (now(), xid)
                    )
                for u in rows(
                    "SELECT id FROM users WHERE role IN ('admin','asset_manager') AND enabled=1"
                ):
                    notify(u["id"], "Equipment " + action, f"/assetpass/assets/{x['asset_id']}")
            elif action == "return":
                if not manager():
                    abort(403)
                if "verified" not in request.form:
                    raise ValueError("Physical verification is required.")
                status = choice("status", ("Available", "Under Repair", "Retired"))
                condition = required("condition")
                db().execute(
                    "UPDATE assignments SET returned_at=?,condition_in=?,return_notes=? WHERE id=?",
                    (now(), condition, request.form.get("notes"), xid),
                )
                db().execute(
                    "UPDATE assets SET status=?,condition=?,retirement_date=? WHERE id=?",
                    (
                        status,
                        condition,
                        datetime.now(timezone.utc).date().isoformat()
                        if status == "Retired"
                        else None,
                        x["asset_id"],
                    ),
                )
                notify(x["user_id"], "Equipment return verified", url_for("my_equipment"))
            else:
                abort(404)
            audit(x["asset_id"], action, request.form.get("notes", ""))
        return redirect(
            url_for("my_equipment") if not manager() else url_for("asset_detail", aid=x["asset_id"])
        )

    @app.route("/assetpass/issues", methods=["GET", "POST"])
    @protected()
    def issues():
        if request.method == "POST":
            aid = int(required("asset_id"))
            asset_or_404(aid)
            if not manager() and not one(
                "SELECT 1 FROM assignments WHERE asset_id=? AND user_id=? AND returned_at IS NULL",
                (aid, g.user["id"]),
            ):
                abort(403)
            with db():
                iid = (
                    db()
                    .execute(
                        "INSERT INTO issues(asset_id,user_id,kind,description,created_at) VALUES(?,?,?,?,?)",
                        (
                            aid,
                            g.user["id"],
                            choice("kind", ("Damage", "Malfunction", "Missing", "Suspected theft")),
                            required("description"),
                            now(),
                        ),
                    )
                    .lastrowid
                )
                audit(aid, "Issue reported", request.form["kind"])
                for u in rows(
                    "SELECT id FROM users WHERE role IN ('admin','asset_manager') AND enabled=1"
                ):
                    notify(u["id"], "New equipment report", url_for("issues"))
            flash(f"Report #{iid} submitted. Photos can be attached from the asset record.")
            return redirect(url_for("issues"))
        items = rows(
            "SELECT i.*,a.asset_tag,u.name employee FROM issues i JOIN assets a ON a.id=i.asset_id JOIN users u ON u.id=i.user_id ORDER BY i.id DESC"
        )
        items = [i for i in items if manager() or i["user_id"] == g.user["id"]]
        return render_template("issues.html", items=items, assets=filtered_assets())

    @app.post("/assetpass/issues/<int:iid>/close")
    @protected("admin", "asset_manager")
    def close_issue(iid):
        with db():
            i = one("SELECT * FROM issues WHERE id=?", (iid,))
            if not i:
                abort(404)
            resolution = required("resolution")
            db().execute(
                "UPDATE issues SET status='Closed',resolution=? WHERE id=?", (resolution, iid)
            )
            audit(i["asset_id"], "Issue resolved", resolution)
            notify(i["user_id"], "Equipment report resolved", url_for("issues"))
        return redirect(url_for("issues"))

    @app.post("/assetpass/assets/<int:aid>/attachments")
    @protected()
    def upload(aid):
        asset_or_404(aid)
        iid = request.form.get("issue_id") or None
        if not manager():
            if not iid or not one(
                "SELECT 1 FROM issues WHERE id=? AND asset_id=? AND user_id=?",
                (iid, aid, g.user["id"]),
            ):
                abort(403)
        if iid and not one("SELECT 1 FROM issues WHERE id=? AND asset_id=?", (iid, aid)):
            abort(400)
        f = request.files.get("file")
        if not f or not f.filename:
            raise ValueError("Choose an image or PDF.")
        content = f.read()
        mime = "application/pdf"
        if content.startswith(b"%PDF-"):
            ext = ".pdf"
        else:
            from PIL import Image, UnidentifiedImageError

            try:
                img = Image.open(BytesIO(content))
                img.verify()
                if img.format not in ("PNG", "JPEG"):
                    raise ValueError("Only PNG, JPEG and PDF are supported.")
                ext = ".png" if img.format == "PNG" else ".jpg"
                mime = "image/png" if ext == ".png" else "image/jpeg"
            except (UnidentifiedImageError, OSError):
                raise ValueError("Invalid attachment.")
        from werkzeug.utils import secure_filename

        key = secrets.token_hex(24) + ext
        path = Path(app.config["DATA_DIR"]) / "uploads" / key
        path.write_bytes(content)
        try:
            with db():
                db().execute(
                    "INSERT INTO attachments(asset_id,issue_id,name,storage_key,mime) VALUES(?,?,?,?,?)",
                    (aid, iid, secure_filename(f.filename) or ("attachment" + ext), key, mime),
                )
                audit(aid, "Attachment added")
        except Exception:
            path.unlink(missing_ok=True)
            raise
        return redirect(url_for("asset_detail", aid=aid))

    @app.get("/assetpass/attachments/<int:fid>")
    @protected()
    def download(fid):
        f = one("SELECT * FROM attachments WHERE id=?", (fid,))
        if not f:
            abort(404)
        asset_or_404(f["asset_id"])
        if (
            f["issue_id"]
            and not manager()
            and not one(
                "SELECT 1 FROM issues WHERE id=? AND user_id=?", (f["issue_id"], g.user["id"])
            )
        ):
            abort(403)
        return send_file(
            Path(app.config["DATA_DIR"]) / "uploads" / f["storage_key"],
            as_attachment=True,
            download_name=f["name"],
            mimetype=f["mime"],
        )

    @app.get("/assetpass/assets/<int:aid>/qr")
    @protected()
    def qr(aid):
        asset_or_404(aid)
        import qrcode

        # Record URL has no employee, price or equipment data.
        base = app.config.get("PUBLIC_BASE_URL") or request.host_url.rstrip("/")
        target = base.rstrip("/") + url_for("asset_detail", aid=aid)
        out = BytesIO()
        qrcode.make(target).save(out, format="PNG")
        out.seek(0)
        return send_file(out, mimetype="image/png")

    @app.get("/assetpass/assets/<int:aid>/label")
    @protected("admin", "asset_manager")
    def label(aid):
        return render_template("label.html", a=asset_or_404(aid))

    @app.get("/assetpass/assignments")
    @app.get("/assetpass/returns")
    @app.get("/assetpass/history")
    @protected()
    def assignments():
        xs = rows(
            "SELECT x.*,a.asset_tag,u.name employee,u.department_id FROM assignments x JOIN assets a ON a.id=x.asset_id JOIN users u ON u.id=x.user_id ORDER BY x.id DESC"
        )
        xs = [
            x
            for x in xs
            if manager()
            or x["user_id"] == g.user["id"]
            or (
                g.user["role"] == "department_manager"
                and g.user["department_id"]
                and x["department_id"] == g.user["department_id"]
            )
        ]
        if request.path.endswith("returns"):
            xs = [x for x in xs if x["return_requested_at"] or x["returned_at"]]
        return render_template(
            "assignments.html",
            items=xs,
            events=rows(
                "SELECT a.*,s.asset_tag,u.name actor FROM audit a LEFT JOIN assets s ON s.id=a.asset_id LEFT JOIN users u ON u.id=a.actor_id ORDER BY a.id DESC"
            )
            if manager() and request.path.endswith("history")
            else [],
            title="Returns"
            if request.path.endswith("returns")
            else "Asset history"
            if request.path.endswith("history")
            else "Assignments & handovers",
        )

    @app.route("/assetpass/clearance", methods=["GET", "POST"])
    @protected("admin", "asset_manager")
    def clearance():
        uid = request.values.get("user_id", "")
        xs = rows(
            "SELECT x.*,a.asset_tag FROM assignments x JOIN assets a ON a.id=x.asset_id WHERE user_id=? AND returned_at IS NULL",
            (uid,),
        )
        if request.method == "POST":
            with db():
                db().execute("BEGIN IMMEDIATE")
                if not one("SELECT 1 FROM users WHERE id=?", (uid,)):
                    abort(404)
                if one("SELECT 1 FROM assignments WHERE user_id=? AND returned_at IS NULL", (uid,)):
                    raise ValueError("All equipment must be physically returned before clearance.")
                db().execute(
                    "INSERT INTO clearances(user_id,completed_by,completed_at) VALUES(?,?,?)",
                    (uid, g.user["id"], now()),
                )
                audit(None, "Equipment clearance", f"Employee #{uid}")
            flash("Equipment clearance recorded. Account remains unchanged.")
        return render_template(
            "clearance.html",
            employees=rows("SELECT id,name FROM users ORDER BY name"),
            items=xs,
            selected=uid,
            completed=rows(
                "SELECT c.*,u.name FROM clearances c JOIN users u ON u.id=c.user_id ORDER BY c.id DESC"
            ),
        )

    @app.get("/assetpass/reports")
    @protected("admin", "asset_manager", "department_manager")
    def reports():
        return render_template("reports.html")

    @app.get("/assetpass/export/<kind>")
    @protected("admin", "asset_manager", "department_manager")
    def export(kind):
        from openpyxl import Workbook

        kinds = (
            "inventory",
            "category",
            "department",
            "assignments",
            "pending",
            "warranty",
            "returns",
            "issues",
        )
        if kind not in kinds:
            abort(404)
        assets = filtered_assets()
        ids = {a["id"] for a in assets}
        wb = Workbook()
        ws = wb.active
        ws.title = "AssetPass"
        if kind in ("inventory", "category", "department", "warranty"):
            fields = [
                "asset_tag",
                "category",
                "manufacturer",
                "model",
                "serial",
                "status",
                "condition",
                "location",
                "warranty_expiration",
            ]
            if manager():
                fields += ["purchase_date", "purchase_cost", "supplier"]
            ws.append(fields + ["employee", "department"])
            for a in assets:
                if kind == "warranty" and not a["warranty_expiration"]:
                    continue
                x = one(
                    "SELECT u.name,d.name department FROM assignments x JOIN users u ON u.id=x.user_id LEFT JOIN departments d ON d.id=u.department_id WHERE x.asset_id=? AND x.returned_at IS NULL",
                    (a["id"],),
                )
                ws.append(
                    [a[f] for f in fields] + [x["name"] if x else "", x["department"] if x else ""]
                )
        elif kind == "issues":
            ws.append(
                ["Asset", "Employee", "Type", "Description", "Reported", "Status", "Resolution"]
            )
            for i in rows(
                "SELECT i.*,a.asset_tag,u.name FROM issues i JOIN assets a ON a.id=i.asset_id JOIN users u ON u.id=i.user_id"
            ):
                if i["asset_id"] in ids and (
                    manager()
                    or one(
                        "SELECT 1 FROM users WHERE id=? AND department_id=?",
                        (i["user_id"], g.user["department_id"]),
                    )
                ):
                    ws.append(
                        [
                            i[k]
                            for k in (
                                "asset_tag",
                                "name",
                                "kind",
                                "description",
                                "created_at",
                                "status",
                                "resolution",
                            )
                        ]
                    )
        else:
            ws.append(
                [
                    "Asset",
                    "Employee",
                    "Assigned",
                    "Confirmed",
                    "Return requested",
                    "Returned",
                    "Condition out",
                    "Condition in",
                ]
            )
            for x in rows(
                "SELECT x.*,a.asset_tag,a.category,u.name,u.department_id FROM assignments x JOIN assets a ON a.id=x.asset_id JOIN users u ON u.id=x.user_id"
            ):
                permitted = manager() or (
                    g.user["department_id"] and x["department_id"] == g.user["department_id"]
                )
                if not permitted:
                    continue
                if request.args.get("category") and x["category"] != request.args["category"]:
                    continue
                if (
                    request.args.get("department")
                    and str(x["department_id"]) != request.args["department"]
                ):
                    continue
                if kind == "pending" and (x["confirmed_at"] or x["returned_at"]):
                    continue
                if kind == "assignments" and x["returned_at"]:
                    continue
                if kind == "returns" and not (x["returned_at"] or x["return_requested_at"]):
                    continue
                ws.append(
                    [
                        x[k]
                        for k in (
                            "asset_tag",
                            "name",
                            "assigned_at",
                            "confirmed_at",
                            "return_requested_at",
                            "returned_at",
                            "condition_out",
                            "condition_in",
                        )
                    ]
                )
        # Prevent spreadsheet formula execution from user-provided text.
        for row in ws:
            for cell in row:
                if isinstance(cell.value, str) and cell.value.startswith(("=", "+", "-", "@")):
                    cell.value = "'" + cell.value
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions
        for col in ws.columns:
            ws.column_dimensions[col[0].column_letter].width = 24
        out = BytesIO()
        wb.save(out)
        out.seek(0)
        return send_file(
            out,
            as_attachment=True,
            download_name=f"Cirrus-AssetPass-{kind}.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
