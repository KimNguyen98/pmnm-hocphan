from flask import Flask, jsonify, url_for
from werkzeug.routing import BaseConverter

app = Flask(__name__)


class ListConverter(BaseConverter):
    # Danh sách số nguyên (có thể âm) cách nhau bởi dấu phẩy
    regex = r"-?\d+(?:,-?\d+)*"

    def to_python(self, value):
        return [int(x) for x in value.split(",")]

    def to_url(self, value):
        return ",".join(str(int(x)) for x in value)


# Đăng ký converter TRƯỚC khi khai báo route
app.url_map.converters["list"] = ListConverter


@app.route("/sum/<list:numbers>")
def sum_numbers(numbers):
    return jsonify({"numbers": numbers, "sum": sum(numbers)})


if __name__ == "__main__":
    with app.test_request_context():
        print(url_for("sum_numbers", numbers=[4, 5, 6]))  # /sum/4,5,6

    app.run(debug=True)