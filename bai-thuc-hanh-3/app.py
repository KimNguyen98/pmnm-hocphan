from flask import Flask, session, render_template

from extensions import db, migrate, csrf


def vnd(value):
    """Định dạng tiền: 95000 -> 95.000 ₫"""
    try:
        return f"{int(round(value or 0)):,}".replace(",", ".") + " ₫"
    except (TypeError, ValueError):
        return "0 ₫"


def create_app():
    app = Flask(__name__)
    app.config.from_pyfile("config.py")

    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)  # bảo vệ CSRF cho mọi form POST

    import models  # noqa: F401  (để Flask-Migrate nhận biết các bảng)

    from routes.shop import shop_bp
    from routes.admin import admin_bp
    app.register_blueprint(shop_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")

    app.jinja_env.filters["vnd"] = vnd

    @app.context_processor
    def inject_globals():
        cart = session.get("cart", {})
        return {
            "cart_count": sum(item["qty"] for item in cart.values()),
            "TRANG_THAI": models.TRANG_THAI,
        }

    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(413)
    def too_large(e):
        from flask import flash, redirect, request
        flash("Ảnh quá lớn, tối đa 2 MB.", "error")
        return redirect(request.referrer or "/admin/books")

    return app


if __name__ == "__main__":
    create_app().run(debug=True)