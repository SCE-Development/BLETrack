from flask import Flask, jsonify, request

from espresense_wrapper import ESPresenseWrapper


app = Flask(__name__)

client = ESPresenseWrapper("http://10.251.10.179")


@app.get("/enroll/start")
def enroll_start():
    device_type = request.args.get("device_type", "phone")
    name = request.args.get("name", "new_device")
    result = client.start_enrollment(device_type=device_type, name=name)
    return jsonify(result)


@app.get("/enroll/cancel")
def enroll_cancel():
    result = client.cancel_enrollment()
    return jsonify(result)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5055, debug=True)
