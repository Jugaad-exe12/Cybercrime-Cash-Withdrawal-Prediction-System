from flask import Flask, render_template, request, jsonify
import csv
import os
import pickle
import json
import urllib.request
from datetime import datetime
from math import radians, sin, cos, sqrt, atan2
import smtplib
from email.message import EmailMessage

# =========================================================
# FLASK CONFIGURATION
# =========================================================

app = Flask(
    __name__,
    template_folder="Frontend",
    static_folder="Frontend"
)

# =========================================================
# BASE PATHS
# =========================================================

BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "Data"
)

MODEL_FILE = os.path.join(
    BASE_DIR,
    "risk_model.pkl"
)

COMPLAINT_FILE = os.path.join(
    DATA_DIR,
    "complaint.csv"
)

HISTORICAL_FILE = os.path.join(
    DATA_DIR,
    "historical_data.csv"
)

REALTIME_FILE = os.path.join(
    DATA_DIR,
    "realtime_transactions.csv"
)

LOCATION_FILE = os.path.join(
    DATA_DIR,
    "location_data.csv"
)

ATM_FILE = os.path.join(
    DATA_DIR,
    "atm_data.csv"
)

POLICE_FILE = os.path.join(
    DATA_DIR,
    "police_stations.csv"
)

BANK_FILE = os.path.join(
    DATA_DIR,
    "bank_data.csv"
)

DETECTED_FILE = os.path.join(
    DATA_DIR,
    "detected_withdrawals.csv"
)

NOTIFICATION_LOG_FILE = os.path.join(
    DATA_DIR,
    "notification_log.csv"
)

# =========================================================
# NOTIFICATION CONFIGURATION
# =========================================================

SMTP_HOST = os.getenv(
    "SMTP_HOST",
    ""
)

SMTP_PORT = int(
    os.getenv(
        "SMTP_PORT",
        "587"
    )
)

SMTP_USER = os.getenv(
    "SMTP_USER",
    ""
)

SMTP_PASSWORD = os.getenv(
    "SMTP_PASSWORD",
    ""
)

BANK_ALERT_EMAIL = os.getenv(
    "BANK_ALERT_EMAIL",
    ""
)

POLICE_ALERT_EMAIL = os.getenv(
    "POLICE_ALERT_EMAIL",
    ""
)

SMS_WEBHOOK_URL = os.getenv(
    "SMS_WEBHOOK_URL",
    ""
)

BANK_ALERT_PHONE = os.getenv(
    "BANK_ALERT_PHONE",
    ""
)

POLICE_ALERT_PHONE = os.getenv(
    "POLICE_ALERT_PHONE",
    ""
)

# =========================================================
# CREATE REQUIRED FILES
# =========================================================

def create_files():

    os.makedirs(
        DATA_DIR,
        exist_ok=True
    )

    if not os.path.exists(
        COMPLAINT_FILE
    ):

        with open(
            COMPLAINT_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "complaint_id",
                "crime_type",
                "crime_datetime",
                "complaint_datetime",
                "amount",
                "victim_location",
                "transaction_id",
                "bank_reference",
                "description"
            ])

    if not os.path.exists(
        DETECTED_FILE
    ):

        with open(
            DETECTED_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "complaint_id",
                "transaction_id",
                "withdrawal_status",
                "withdrawal_location",
                "latitude",
                "longitude",
                "detected_at"
            ])

    if not os.path.exists(
        NOTIFICATION_LOG_FILE
    ):

        with open(
            NOTIFICATION_LOG_FILE,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([
                "timestamp",
                "alert_type",
                "channel",
                "recipient",
                "status",
                "message"
            ])

# =========================================================
# LOAD MACHINE LEARNING MODEL
# =========================================================

model = None

try:

    if os.path.exists(
        MODEL_FILE
    ):

        with open(
            MODEL_FILE,
            "rb"
        ) as file:

            model = pickle.load(
                file
            )

        print(
            "ML model loaded successfully."
        )

    else:

        print(
            "risk_model.pkl not found."
        )

        print(
            "Fallback risk calculation will be used."
        )

except Exception as error:

    print(
        "Could not load ML model:",
        error
    )

    model = None


# =========================================================
# NOTIFICATION LOG
# =========================================================

def log_notification(
    alert_type,
    channel,
    recipient,
    status,
    message
):

    create_files()

    try:

        with open(
            NOTIFICATION_LOG_FILE,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow([

                datetime.now().strftime(
                    "%Y-%m-%d %H:%M:%S"
                ),

                alert_type,

                channel,

                recipient,

                status,

                message

            ])

    except Exception as error:

        print(
            "Notification logging error:",
            error
        )

# =========================================================
# SEND EMAIL
# =========================================================

def send_email_alert(
    recipient,
    subject,
    body,
    alert_type="SYSTEM"
):

    if not recipient:

        return {
            "status": "NOT_CONFIGURED",
            "message":
                "Email recipient is not configured."
        }

    if not SMTP_HOST:

        log_notification(

            alert_type,
            "EMAIL",
            recipient,
            "NOT_CONFIGURED",
            "SMTP_HOST is not configured."

        )

        return {
            "status": "NOT_CONFIGURED",
            "message":
                "SMTP configuration is missing."
        }

    if not SMTP_USER:

        return {
            "status": "NOT_CONFIGURED",
            "message":
                "SMTP user is not configured."
        }

    if not SMTP_PASSWORD:

        return {
            "status": "NOT_CONFIGURED",
            "message":
                "SMTP password is not configured."
        }

    try:

        message = EmailMessage()

        message["From"] = SMTP_USER

        message["To"] = recipient

        message["Subject"] = subject

        message.set_content(
            body
        )

        with smtplib.SMTP(
            SMTP_HOST,
            SMTP_PORT,
            timeout=20
        ) as server:

            server.starttls()

            server.login(
                SMTP_USER,
                SMTP_PASSWORD
            )

            server.send_message(
                message
            )

        log_notification(

            alert_type,
            "EMAIL",
            recipient,
            "SENT",
            "Email notification sent."

        )

        return {
            "status": "SENT",
            "message":
                "Email notification sent."
        }

    except Exception as error:

        print(
            "Email notification error:",
            error
        )

        log_notification(

            alert_type,
            "EMAIL",
            recipient,
            "FAILED",
            str(error)

        )

        return {
            "status": "FAILED",
            "message": str(error)
        }

# =========================================================
# SEND SMS THROUGH WEBHOOK
# =========================================================

def send_sms_alert(
    phone_number,
    message,
    alert_type="SYSTEM"
):

    if not phone_number:

        return {
            "status": "NOT_CONFIGURED",
            "message":
                "Phone number is not configured."
        }

    if not SMS_WEBHOOK_URL:

        log_notification(

            alert_type,
            "SMS",
            phone_number,
            "NOT_CONFIGURED",
            "SMS webhook is not configured."

        )

        return {
            "status": "NOT_CONFIGURED",
            "message":
                "SMS webhook is not configured."
        }

    try:

        payload = {

            "to":
                phone_number,

            "message":
                message

        }

        encoded_data = json.dumps(
            payload
        ).encode(
            "utf-8"
        )

        request_object = urllib.request.Request(

            SMS_WEBHOOK_URL,

            data=encoded_data,

            headers={
                "Content-Type":
                    "application/json"
            },

            method="POST"

        )

        with urllib.request.urlopen(
            request_object,
            timeout=20
        ) as response:

            response_data = response.read().decode(
                "utf-8"
            )

        log_notification(

            alert_type,
            "SMS",
            phone_number,
            "SENT",
            response_data[:500]

        )

        return {
            "status": "SENT",
            "message":
                "SMS webhook notification sent."
        }

    except Exception as error:

        print(
            "SMS notification error:",
            error
        )

        log_notification(

            alert_type,
            "SMS",
            phone_number,
            "FAILED",
            str(error)

        )

        return {
            "status": "FAILED",
            "message": str(error)
        }

# =========================================================
# HIGH RISK NOTIFICATION
# =========================================================

def send_high_risk_notifications(
    complaint_id,
    transaction_id,
    amount,
    location,
    risk,
    latitude="",
    longitude=""
):

    if str(risk).upper() != "HIGH":

        return {
            "status":
                "NOT_REQUIRED",
            "message":
                "Notification is only triggered for HIGH risk."
        }

    alert_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    subject = (
        "HIGH RISK CYBERCRIME ALERT - "
        + str(transaction_id)
    )

    body = f"""
Cybercrime Predictive Analytics System

HIGH RISK ALERT

Complaint ID: {complaint_id}
Transaction ID: {transaction_id}
Transaction Amount: Rs.{amount}
Risk Level: {risk}

Withdrawal Location: {location}

Latitude: {latitude}
Longitude: {longitude}

Alert Time: {alert_time}

This is an automated alert generated by the
Cybercrime Predictive Analytics System.

Please verify the transaction through the
authorized investigation workflow.
"""

    bank_email_result = send_email_alert(

        BANK_ALERT_EMAIL,

        subject,

        body,

        "BANK_ALERT"

    )

    police_email_result = send_email_alert(

        POLICE_ALERT_EMAIL,

        subject,

        body,

        "POLICE_ALERT"

    )

    bank_sms_result = send_sms_alert(

        BANK_ALERT_PHONE,

        (
            "HIGH RISK CYBERCRIME ALERT. "
            f"Transaction {transaction_id}, "
            f"Amount Rs.{amount}, "
            f"Location {location}."
        ),

        "BANK_ALERT"

    )

    police_sms_result = send_sms_alert(

        POLICE_ALERT_PHONE,

        (
            "HIGH RISK CYBERCRIME ALERT. "
            f"Transaction {transaction_id}, "
            f"Amount Rs.{amount}, "
            f"Location {location}."
        ),

        "POLICE_ALERT"

    )

    return {

        "status":
            "PROCESSED",

        "bank": {

            "email":
                bank_email_result,

            "sms":
                bank_sms_result

        },

        "police": {

            "email":
                police_email_result,

            "sms":
                police_sms_result

        },

        "alert_time":
            alert_time

    }

# =========================================================
# HOME
# =========================================================

@app.route("/")
def home():

    create_files()

    return render_template(
        "index.html"
    )

# =========================================================
# PREDICT
# =========================================================

@app.route(
    "/predict",
    methods=["POST"]
)
def predict():

    create_files()

    complaint_id = request.form.get(
        "complaint_id",
        ""
    ).strip()

    transaction_id = request.form.get(
        "transaction_id",
        ""
    ).strip()

    amount = request.form.get(
        "amount",
        ""
    ).strip()

    district = request.form.get(
        "district",
        ""
    ).strip()

    latitude = request.form.get(
        "latitude",
        ""
    ).strip()

    longitude = request.form.get(
        "longitude",
        ""
    ).strip()

    if not complaint_id:

        return render_template(
            "index.html",
            error="Complaint ID is required."
        )

    if not amount:

        return render_template(
            "index.html",
            error="Transaction amount is required."
        )

    try:

        amount_value = float(
            amount
        )

    except ValueError:

        return render_template(
            "index.html",
            error="Transaction amount must be a number."
        )

    # -----------------------------------------------------
    # RISK PREDICTION
    # -----------------------------------------------------

    risk = "LOW"

    model_used = False

    if model is not None:

        try:

            prediction = model.predict(
                [[amount_value]]
            )[0]

            prediction_text = str(
                prediction
            ).upper()

            if (
                "HIGH" in prediction_text
                or prediction_text == "2"
            ):

                risk = "HIGH"

            elif (
                "MEDIUM" in prediction_text
                or prediction_text == "1"
            ):

                risk = "MEDIUM"

            else:

                risk = "LOW"

            model_used = True

        except Exception as error:

            print(
                "ML prediction failed:",
                error
            )

            model_used = False

    # -----------------------------------------------------
    # FALLBACK RISK
    # -----------------------------------------------------

    if not model_used:

        if amount_value >= 50000:

            risk = "HIGH"

        elif amount_value >= 20000:

            risk = "MEDIUM"

        else:

            risk = "LOW"

    withdrawal_location = (

        district
        if district
        else "Location unavailable"

    )

    timestamp = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    notification = {
        "status":
            "NOT_REQUIRED"
    }

    if risk == "HIGH":

        notification = send_high_risk_notifications(

            complaint_id,

            transaction_id,

            amount,

            withdrawal_location,

            risk,

            latitude,

            longitude

        )

    return render_template(

        "index.html",

        complaint_id=complaint_id,

        transaction_id=transaction_id,

        amount=amount,

        district=district,

        latitude=latitude,

        longitude=longitude,

        withdrawal_location=
            withdrawal_location,

        risk=risk,

        timestamp=timestamp,

        notification=notification

    )

# =========================================================
# SUBMIT COMPLAINT
# =========================================================

@app.route(
    "/submit_complaint",
    methods=["POST"]
)
def submit_complaint():

    create_files()

    data = request.get_json(
        silent=True
    ) or {}

    complaint_id = (
        "CC-"
        + datetime.now().strftime(
            "%Y%m%d%H%M%S"
        )
    )

    row = [

        complaint_id,

        data.get(
            "crime_type",
            ""
        ),

        data.get(
            "crime_datetime",
            ""
        ),

        data.get(
            "complaint_datetime",
            ""
        ),

        data.get(
            "amount",
            ""
        ),

        data.get(
            "victim_location",
            ""
        ),

        data.get(
            "transaction_id",
            ""
        ),

        data.get(
            "bank_reference",
            ""
        ),

        data.get(
            "description",
            ""
        )

    ]

    with open(
        COMPLAINT_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow(row)

    return jsonify({

        "status":
            "SUCCESS",

        "complaint_id":
            complaint_id,

        "message":
            "Complaint successfully registered."

    })

# =========================================================
# REAL-TIME ALERT
# =========================================================

@app.route(
    "/realtime_alert"
)
def realtime_alert():

    suspicious = []

    if not os.path.exists(
        REALTIME_FILE
    ):

        return jsonify([])

    with open(
        REALTIME_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            try:

                amount = float(
                    row.get(
                        "amount",
                        0
                    )
                )

            except (
                ValueError,
                TypeError
            ):

                amount = 0

            status = row.get(
                "status",
                ""
            ).strip().lower()


            if (
                status == "pending"
                and amount >= 20000
            ):

                row["risk"] = "HIGH RISK"

                suspicious.append(
                    row
                )

    return jsonify(
        suspicious
    )

# =========================================================
# DISTANCE CALCULATION
# =========================================================

def calculate_distance(
    lat1,
    lon1,
    lat2,
    lon2
):

    R = 6371.0

    dlat = radians(
        lat2 - lat1
    )

    dlon = radians(
        lon2 - lon1
    )

    a = (

        sin(dlat / 2) ** 2

        +

        cos(radians(lat1))
        *
        cos(radians(lat2))
        *
        sin(dlon / 2) ** 2

    )

    c = 2 * atan2(
        sqrt(a),
        sqrt(1 - a)
    )

    return R * c

# =========================================================
# NEARBY ATMS
# =========================================================

@app.route(
    "/nearby_atms"
)
def nearby_atms():

    reference_lat = 22.5726

    reference_lon = 88.3639

    atms = []

    if not os.path.exists(
        ATM_FILE
    ):

        return jsonify([])

    with open(
        ATM_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            try:

                lat = float(
                    row.get(
                        "latitude",
                        0
                    )
                )

                lon = float(
                    row.get(
                        "longitude",
                        0
                    )
                )

            except (
                ValueError,
                TypeError
            ):

                continue

            distance = calculate_distance(

                reference_lat,
                reference_lon,
                lat,
                lon

            )

            row["distance_km"] = round(
                distance,
                2
            )

            atms.append(
                row
            )

    return jsonify(
        atms
    )

# =========================================================
# POLICE STATIONS
# =========================================================

@app.route(
    "/police_stations"
)
def police_stations():

    stations = []

    if not os.path.exists(
        POLICE_FILE
    ):

        return jsonify([])
    
    with open(
        POLICE_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            stations.append(
                row
            )

    return jsonify(
        stations
    )

# =========================================================
# GIS WITHDRAWALS
# =========================================================

@app.route(
    "/gis_withdrawals"
)
def gis_withdrawals():

    create_files()

    locations = []

    if not os.path.exists(
        DETECTED_FILE
    ):

        return jsonify([])

    with open(
        DETECTED_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            latitude = row.get(
                "latitude",
                ""
            ).strip()

            longitude = row.get(
                "longitude",
                ""
            ).strip()

            if (
                not latitude
                or not longitude
            ):

                continue

            try:

                latitude = float(
                    latitude
                )

                longitude = float(
                    longitude
                )

            except (
                ValueError,
                TypeError
            ):

                continue

            locations.append({

                "complaint_id":
                    row.get(
                        "complaint_id",
                        ""
                    ),

                "transaction_id":
                    row.get(
                        "transaction_id",
                        ""
                    ),

                "status":
                    row.get(
                        "withdrawal_status",
                        ""
                    ),

                "location":
                    row.get(
                        "withdrawal_location",
                        ""
                    ),

                "latitude":
                    latitude,

                "longitude":
                    longitude,

                "detected_at":
                    row.get(
                        "detected_at",
                        ""
                    )
            })

    return jsonify(
        locations
    )

# =========================================================
# DELAYED COMPLAINT CHECK
# =========================================================

@app.route(
    "/delayed_complaint_check",
    methods=["POST"]
)
def delayed_complaint_check():

    create_files()

    data = request.get_json(
        silent=True
    ) or {}

    complaint_id = str(
        data.get(
            "complaint_id",
            ""
        )
    ).strip()

    transaction_id = str(
        data.get(
            "transaction_id",
            ""
        )
    ).strip()

    crime_datetime = str(
        data.get(
            "crime_datetime",
            ""
        )
    ).strip()

    complaint_datetime = str(
        data.get(
            "complaint_datetime",
            ""
        )
    ).strip()

    if not complaint_id:

        return jsonify({
            "status": "ERROR",
            "message":
                "Complaint ID is required."
        }), 400

    if not transaction_id:

        return jsonify({
            "status": "ERROR",
            "message":
                "Transaction ID is required."
        }), 400

    if not crime_datetime:

        return jsonify({
            "status": "ERROR",
            "message":
                "Crime date/time is required."
        }), 400

    if not complaint_datetime:

        return jsonify({
            "status": "ERROR",
            "message":
                "Complaint date/time is required."
        }), 400

    try:

        crime_time = datetime.fromisoformat(
            crime_datetime
        )

        complaint_time = datetime.fromisoformat(
            complaint_datetime
        )

    except ValueError:

        return jsonify({
            "status": "ERROR",
            "message":
                "Invalid date/time format."
        }), 400

    delay_seconds = (
        complaint_time
        - crime_time
    ).total_seconds()

    delay_hours = round(
        delay_seconds / 3600,
        2
    )

    if delay_seconds < 0:

        return jsonify({
            "status": "ERROR",
            "message":
                "Complaint time cannot be earlier than crime time."
        }), 400

    if delay_hours < 2:

        return jsonify({

            "status":
                "EARLY_COMPLAINT",

            "complaint_id":
                complaint_id,

            "transaction_id":
                transaction_id,

            "delay_hours":
                delay_hours,

            "withdrawal_status":
                "CHECK_NOT_REQUIRED",

            "message":
                "Complaint was received within 2 hours."

        })

    transaction = None

    if os.path.exists(
        REALTIME_FILE
    ):

        with open(
            REALTIME_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(
                file
            )

            for row in reader:

                if (
                    row.get(
                        "transaction_id",
                        ""
                    ).strip()
                    == transaction_id
                ):

                    transaction = row

                    break

    if transaction is None:

        if os.path.exists(
            HISTORICAL_FILE
        ):

            with open(
                HISTORICAL_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                reader = csv.DictReader(
                    file
                )


                for row in reader:

                    if (
                        row.get(
                            "transaction_id",
                            ""
                        ).strip()
                        == transaction_id
                    ):

                        transaction = row

                        break

    if transaction is None:

        return jsonify({

            "status":
                "TRANSACTION_NOT_FOUND",

            "complaint_id":
                complaint_id,

            "transaction_id":
                transaction_id,

            "delay_hours":
                delay_hours,

            "withdrawal_status":
                "UNKNOWN",

            "message":
                "Transaction was not found."

        })

    transaction_status = (
        transaction.get(
            "status",
            ""
        ).strip().lower()
    )

    withdrawn_values = [

        "withdrawn",
        "success",
        "successful",
        "completed",
        "cash withdrawn"

    ]

    if (
        transaction_status
        not in withdrawn_values
    ):

        return jsonify({

            "status":
                "NOT_WITHDRAWN",

            "complaint_id":
                complaint_id,

            "transaction_id":
                transaction_id,

            "delay_hours":
                delay_hours,

            "withdrawal_status":
                "NOT WITHDRAWN",

            "message":
                "Money has not been marked as withdrawn."

        })

    withdrawal_location = (
        transaction.get(
            "withdrawal_location",
            ""
        ).strip()
    )

    if not withdrawal_location:

        withdrawal_location = (
            transaction.get(
                "location",
                ""
            ).strip()
        )

    if not withdrawal_location:

        withdrawal_location = "Unknown"

    latitude = transaction.get(
        "latitude",
        ""
    ).strip()

    longitude = transaction.get(
        "longitude",
        ""
    ).strip()

    if (
        not latitude
        or not longitude
    ):

        if os.path.exists(
            LOCATION_FILE
        ):

            with open(
                LOCATION_FILE,
                "r",
                encoding="utf-8"
            ) as file:

                reader = csv.DictReader(
                    file
                )

                for row in reader:

                    location_name = row.get(
                        "location",
                        ""
                    ).strip()

                    if (
                        location_name.lower()
                        ==
                        withdrawal_location.lower()
                    ):

                        latitude = row.get(
                            "latitude",
                            ""
                        ).strip()

                        longitude = row.get(
                            "longitude",
                            ""
                        ).strip()

                        break

    detected_at = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    with open(
        DETECTED_FILE,
        "a",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([

            complaint_id,
            transaction_id,
            "Withdrawn",
            withdrawal_location,
            latitude,
            longitude,
            detected_at

        ])

    notification = send_high_risk_notifications(

        complaint_id,

        transaction_id,

        transaction.get(
            "amount",
            ""
        ),

        withdrawal_location,

        "HIGH",

        latitude,

        longitude

    )

    return jsonify({

        "status":
            "WITHDRAWN_DETECTED",

        "complaint_id":
            complaint_id,

        "transaction_id":
            transaction_id,

        "delay_hours":
            delay_hours,

        "withdrawal_status":
            "WITHDRAWN",

        "withdrawal_location":
            withdrawal_location,

        "latitude":
            latitude,

        "longitude":
            longitude,

        "detected_at":
            detected_at,

        "notification":
            notification,

        "message":
            "Withdrawal detected and notification workflow processed."

    })

# =========================================================
# DETECTED WITHDRAWALS
# =========================================================

@app.route(
    "/detected_withdrawals"
)
def detected_withdrawals():

    create_files()

    withdrawals = []

    if not os.path.exists(
        DETECTED_FILE
    ):

        return jsonify([])

    with open(
        DETECTED_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            withdrawals.append(
                row
            )

    return jsonify(
        withdrawals
    )

# =========================================================
# RISK SCORE
# =========================================================

@app.route(
    "/risk_score"
)
def risk_score():

    score = 0

    highest_amount = 0

    pending_count = 0

    withdrawn_count = 0

    if os.path.exists(
        REALTIME_FILE
    ):

        with open(
            REALTIME_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(
                file
            )

            for row in reader:

                try:

                    amount = float(
                        row.get(
                            "amount",
                            0
                        )
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    amount = 0

                highest_amount = max(
                    highest_amount,
                    amount
                )

                if (
                    row.get(
                        "status",
                        ""
                    ).strip().lower()
                    == "pending"
                ):

                    pending_count += 1

    if highest_amount >= 50000:

        score += 30

    elif highest_amount >= 20000:

        score += 20

    if pending_count > 0:

        score += 20

    if os.path.exists(
        DETECTED_FILE
    ):

        with open(
            DETECTED_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(
                file
            )

            for row in reader:

                withdrawn_count += 1

    if withdrawn_count >= 5:

        score += 20

    score = min(
        score,
        100
    )

    if score >= 70:

        level = "HIGH"

    elif score >= 40:

        level = "MEDIUM"

    else:

        level = "LOW"

    return jsonify({

        "score":
            score,

        "level":
            level

    })

# =========================================================
# POLICE + BANK ALERT
# =========================================================

@app.route(
    "/police_alert"
)
def police_alert():

    incident_lat = 22.5726

    incident_lon = 88.3639

    nearest_station = None

    smallest_distance = float(
        "inf"
    )

    if os.path.exists(
        POLICE_FILE
    ):

        with open(
            POLICE_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(
                file
            )

            for row in reader:

                try:

                    lat = float(
                        row.get(
                            "latitude",
                            0
                        )
                    )

                    lon = float(
                        row.get(
                            "longitude",
                            0
                        )
                    )

                except (
                    ValueError,
                    TypeError
                ):

                    continue

                distance = calculate_distance(

                    incident_lat,
                    incident_lon,
                    lat,
                    lon

                )

                if distance < smallest_distance:

                    smallest_distance = distance

                    nearest_station = row

    if nearest_station:

        police_status = (
            "ALERT GENERATED"
        )

        station_name = (
            nearest_station.get(
                "station_name",
                "Unknown"
            )
        )

        police_distance = round(
            smallest_distance,
            2
        )

    else:

        police_status = (
            "NO POLICE STATION DATA"
        )

        station_name = "Unknown"

        police_distance = None

    bank_branch = None

    if os.path.exists(
        BANK_FILE
    ):

        with open(
            BANK_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            reader = csv.DictReader(
                file
            )

            for row in reader:

                bank_branch = row

                break

    if bank_branch:

        bank_status = (
            "ALERT GENERATED"
        )

        bank_branch_name = (
            bank_branch.get(
                "branch",
                "Unknown"
            )
        )

    else:

        bank_status = (
            "NO BANK DATA"
        )

        bank_branch_name = "Unknown"

    alert_time = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return jsonify({

        "status":
            "SUCCESS",

        "alert_time":
            alert_time,

        "police_alert": {

            "status":
                police_status,

            "station_name":
                station_name,

            "distance_km":
                police_distance

        },

        "bank_alert": {

            "status":
                bank_status,

            "branch":
                bank_branch_name

        }

    })

# =========================================================
# TEST NOTIFICATION
#
# IMPORTANT:
# GET + POST BOTH ALLOWED
#
# Therefore browser address bar will NOT give 405.
# =========================================================

@app.route(
    "/test_notification",
    methods=["GET", "POST"]
)
def test_notification():

    result = send_high_risk_notifications(

        "TEST-COMPLAINT",

        "TEST-TRANSACTION",

        "75000",

        "Test Location",

        "HIGH",

        "22.5726",

        "88.3639"

    )

    return jsonify({

        "test":
            True,

        "message":
            "Notification test completed.",

        "result":
            result

    })

# =========================================================
# NOTIFICATION STATUS
# =========================================================

@app.route(
    "/notification_status"
)
def notification_status():

    create_files()

    notifications = []

    if not os.path.exists(
        NOTIFICATION_LOG_FILE
    ):

        return jsonify([])

    with open(
        NOTIFICATION_LOG_FILE,
        "r",
        encoding="utf-8"
    ) as file:

        reader = csv.DictReader(
            file
        )

        for row in reader:

            notifications.append(
                row
            )

    return jsonify(
        notifications
    )

# =========================================================
# GIS MAP
# =========================================================

@app.route(
    "/gis_map"
)
def gis_map():

    return render_template(
        "heatmap.html"
    )

# =========================================================
# HEALTH CHECK
# =========================================================

@app.route(
    "/health"
)
def health():

    return jsonify({

        "status":
            "ONLINE",

        "system":
            "Cybercrime Predictive Analytics System",

        "notification": {

            "email":
                bool(SMTP_HOST),

            "sms":
                bool(SMS_WEBHOOK_URL)

        },

        "time":
            datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            )

    })

# =========================================================
# ERROR HANDLERS
# =========================================================

@app.errorhandler(404)
def page_not_found(error):

    return jsonify({

        "status":
            "ERROR",

        "error":
            "404",

        "message":
            "Requested URL was not found."

    }), 404

@app.errorhandler(405)
def method_not_allowed(error):

    return jsonify({

        "status":
            "ERROR",

        "error":
            "405",

        "message":
            "HTTP method is not allowed for this URL."

    }), 405

@app.errorhandler(500)
def internal_server_error(error):

    return jsonify({

        "status":
            "ERROR",

        "error":
            "500",

        "message":
            "Internal server error."

    }), 500

# =========================================================
# START APPLICATION
# =========================================================

if __name__ == "__main__":

    create_files()

    print()
    print(
        "=============================================="
    )
    print(
        " Cybercrime Predictive Analytics System"
    )
    print(
        "=============================================="
    )
    print(
        "Server:"
    )
    print(
        "http://127.0.0.1:5000"
    )
    print(
        "=============================================="
    )
    print(
        "Health:"
    )
    print(
        "http://127.0.0.1:5000/health"
    )
    print(
        "=============================================="
    )
    print(
        "Notification Test:"
    )
    print(
        "http://127.0.0.1:5000/test_notification"
    )
    print(
        "=============================================="
    )
    print(
        "Email configured:",
        bool(SMTP_HOST)
    )
    print(
        "SMS configured:",
        bool(SMS_WEBHOOK_URL)
    )
    print(
        "=============================================="
    )
    print()

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )