import os
import time
import logging
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from questions import EASY, INTERMEDIATE, ADVANCED


TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID")

BASE_URL = f"https://tapi.bale.ai/bot{TOKEN}/"
BACKEND = os.getenv("DJANGO_API_URL", "http://backend:8000/api/")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s"
)

logger = logging.getLogger("bale_bot")


session = requests.Session()

retry = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[500, 502, 503, 504],
)

adapter = HTTPAdapter(max_retries=retry)

session.mount("https://", adapter)
session.mount("http://", adapter)

user_states = {}


def send_message(chat_id, text, buttons=None):

    data = {
        "chat_id": chat_id,
        "text": text
    }

    if buttons:
        data["reply_markup"] = {
            "inline_keyboard": buttons
        }

    for attempt in range(3):
        try:
            r = session.post(
                BASE_URL + "sendMessage",
                json=data,
                timeout=10
            )

            if r.status_code == 200:
                return

            logger.error(f"sendMessage error {r.status_code}: {r.text}")

        except requests.exceptions.RequestException as e:
            logger.error(f"send_message attempt {attempt+1} failed: {e}")

        time.sleep(2)

def main_menu(chat_id):

    buttons = [
        [{"text": "📝 آزمون تعیین سطح", "callback_data": "exam"}],
        [{"text": "👤 پروفایل من", "callback_data": "profile"}],
        [{"text": "✏️ ویرایش اطلاعات", "callback_data": "edit"}],
    ]

    send_message(
        chat_id,
        "🏠 منوی اصلی\n\nیکی از گزینه‌های زیر را انتخاب کنید:",
        buttons
    )


def send_question(chat_id, questions, index):

    q = questions[index]

    buttons = [
        [{"text": opt, "callback_data": f"ans_{index}_{i}"}]
        for i, opt in enumerate(q["options"])
    ]

    send_message(
        chat_id,
        f"❓ سوال {index+1}\n\n{q['question']}",
        buttons
    )


def register_backend(chat_id, name, phone):

    payload = {
        "bale_id": chat_id,
        "name": name,
        "phone": phone
    }

    try:
        session.post(BACKEND + "register/", json=payload, timeout=10)
    except Exception as e:
        logger.exception("register_backend error", extra={"error": str(e)})


def update_backend(chat_id, data):

    try:
        session.patch(
            BACKEND + f"user/update/{chat_id}/",
            json=data,
            timeout=10
        )
    except Exception as e:
        logger.exception("update_backend error", extra={"error": str(e)})


def get_profile(chat_id):

    try:
        resp = session.get(
            BACKEND + f"user/{chat_id}/",
            timeout=10
        )

        if resp.status_code == 200:
            return resp.json()

    except Exception as e:
        logger.exception("get_profile error", extra={"error": str(e)})

    return None


def save_exam(chat_id, score, exam_level):

    payload = {
        "bale_id": chat_id,
        "score": score,
        "exam_level": exam_level
    }

    try:
        session.post(
            BACKEND + "exam/result/",
            json=payload,
            timeout=10
        )
    except Exception as e:
        logger.exception("save_exam error", extra={"error": str(e)})


def handle_message(msg):

    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")

    if text == "/start":
        user_states[chat_id] = {"step": "name"}
        send_message(
            chat_id,
            "سلام 👋\n\nبه سامانه *آزمون تعیین سطح* خوش آمدید.\n\n"
            "لطفاً *نام کامل* خود را وارد کنید:"
        )
        return

    if chat_id in user_states:

        state = user_states[chat_id]

        if state["step"] == "name":
            state["name"] = text
            state["step"] = "phone"

            send_message(
                chat_id,
                "عالی! 🙌\n\nحالا لطفاً *شماره تماس* خود را وارد کنید:"
            )
            return

        if state["step"] == "phone":

            state["phone"] = text

            register_backend(chat_id, state["name"], state["phone"])

            send_message(
                chat_id,
                "✅ ثبت‌نام شما با موفقیت انجام شد!\n\nبه سیستم آزمون خوش آمدید 🌟"
            )

            del user_states[chat_id]

            main_menu(chat_id)

            return

        if state["step"] == "edit_name":

            update_backend(chat_id, {"name": text})

            send_message(
                chat_id,
                "✅ نام شما با موفقیت بروزرسانی شد."
            )

            del user_states[chat_id]

            main_menu(chat_id)

            return

        if state["step"] == "edit_phone":

            update_backend(chat_id, {"phone": text})

            send_message(
                chat_id,
                "✅ شماره تماس با موفقیت بروزرسانی شد."
            )

            del user_states[chat_id]

            main_menu(chat_id)

            return


def handle_callback(cb):

    chat_id = cb["message"]["chat"]["id"]
    data = cb["data"]

    if data == "exam":

        buttons = [
            [{"text": "🟢 آسان", "callback_data": "level_easy"}],
            [{"text": "🟡 متوسط", "callback_data": "level_inter"}],
            [{"text": "🔴 پیشرفته", "callback_data": "level_adv"}],
        ]

        send_message(
            chat_id,
            "🎯 انتخاب سطح آزمون\n\nلطفاً سطح مورد نظر را انتخاب کنید:",
            buttons
        )

        return

    if data == "profile":

        p = get_profile(chat_id)

        if not p:
            send_message(chat_id, "❌ پروفایل یافت نشد.")
            return

        exam_level = p.get("last_exam_level", "ثبت نشده")
        score = p.get("score", "ثبت نشده")

        text = f"""
👤 پروفایل کاربری

📝 نام: {p.get('name','---')}
📱 شماره تماس: {p.get('phone','---')}

📊 آخرین آزمون
▫️ سطح آزمون: {exam_level}
▫️ امتیاز: {score}

برای شرکت در آزمون جدید از منوی اصلی استفاده کنید.
"""

        send_message(chat_id, text)

        return

    if data == "edit":

        buttons = [
            [{"text": "✏️ ویرایش نام", "callback_data": "edit_name"}],
            [{"text": "📱 ویرایش شماره", "callback_data": "edit_phone"}],
        ]

        send_message(
            chat_id,
            "✏️ ویرایش اطلاعات\n\nکدام مورد را می‌خواهید تغییر دهید؟",
            buttons
        )

        return

    if data == "edit_name":

        user_states[chat_id] = {"step": "edit_name"}

        send_message(
            chat_id,
            "🆕 لطفاً *نام جدید* را وارد کنید:"
        )

        return

    if data == "edit_phone":

        user_states[chat_id] = {"step": "edit_phone"}

        send_message(
            chat_id,
            "🆕 لطفاً *شماره تماس جدید* را وارد کنید:"
        )

        return

    if data == "level_easy":

        user_states[chat_id] = {
            "questions": EASY,
            "index": 0,
            "score": 0,
            "level": "Easy"
        }

        send_question(chat_id, EASY, 0)

        return

    if data == "level_inter":

        user_states[chat_id] = {
            "questions": INTERMEDIATE,
            "index": 0,
            "score": 0,
            "level": "Intermediate"
        }

        send_question(chat_id, INTERMEDIATE, 0)

        return

    if data == "level_adv":

        user_states[chat_id] = {
            "questions": ADVANCED,
            "index": 0,
            "score": 0,
            "level": "Advanced"
        }

        send_question(chat_id, ADVANCED, 0)

        return

    if data.startswith("ans"):

        _, q_index, ans = data.split("_")

        q_index = int(q_index)
        ans = int(ans)

        st = user_states.get(chat_id)

        if not st:
            return

        q = st["questions"][q_index]

        if ans == q["answer"]:
            st["score"] += 1

        st["index"] += 1

        if st["index"] < len(st["questions"]):

            send_question(chat_id, st["questions"], st["index"])

        else:

            score = st["score"]

            send_message(
                chat_id,
                f"🎉 آزمون به پایان رسید!\n\n"
                f"📌 سطح آزمون: {st['level']}\n"
                f"🏆 امتیاز شما: {score}\n\n"
                "از شرکت شما در آزمون متشکریم 🙏"
            )

            save_exam(chat_id, score, st["level"])

            profile = get_profile(chat_id) or {}

            name = profile.get("name", "نامشخص")
            phone = profile.get("phone", "نامشخص")

            admin_text = f"""
🚨 کاربر جدید آزمون داد

👤 نام: {name}
📱 شماره: {phone}
🆔 user_id: {chat_id}

📊 نتیجه آزمون
▫️ سطح آزمون: {st['level']}
▫️ امتیاز: {score}
"""

            if ADMIN_ID:
                send_message(ADMIN_ID, admin_text)

            del user_states[chat_id]

            main_menu(chat_id)


def main():
    offset = None

    while True:
        params = {"timeout": 100}
        if offset:
            params["offset"] = offset

        try:
            r = session.get(BASE_URL + "getUpdates", params=params, timeout=120)

            if r.status_code != 200:
                logger.error(f"Bad status code: {r.status_code}, text={r.text}")
                time.sleep(5)
                continue

            if not r.text.strip():
                logger.error("Empty response from Bale API")
                time.sleep(5)
                continue

            try:
                data = r.json()
            except Exception:
                logger.error(f"JSON decode error. Raw response:\n{r.text}")
                time.sleep(5)
                continue

        except Exception as e:
            logger.exception("getUpdates error", extra={"error": str(e)})
            time.sleep(5)
            continue

        updates = data.get("result", [])

        for up in updates:
            offset = up["update_id"] + 1
            if "message" in up:
                handle_message(up["message"])
            if "callback_query" in up:
                handle_callback(up["callback_query"])

        time.sleep(1)



if __name__ == "__main__":
    main()
