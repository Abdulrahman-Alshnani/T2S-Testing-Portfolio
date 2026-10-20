"""
MANUAL SCRIPT — not part of the pytest suite.

Run directly with `python test_api.py` to send a quick HTTP smoke-test
to a running T2S server. Not collected by pytest.
"""
import requests
import json
import time

# رابط الـ API المحلي الخاص بك
URL = "http://127.0.0.1:8000/api/v1/translate/"

# النص التجريبي المرسل (يحتوي على كلمات مركبة وكلمات تحتاج معالجة دلالية)
payload = {
    "text": "السلام عليكم ورحمة الله وبركاته كرة السلة"
}

# محاكاة هيدرز متصفح الكروم القادم من إضافة (Extension)
headers = {
    "Content-Type": "application/json",
    "Origin": "chrome-extension://abcdefghijklmnopqrstuvwxyz"
}

print("🚀 جاري إرسال طلب فحص لـ الـ API الباك آيند...")
start_time = time.time()

try:
    response = requests.post(URL, data=json.dumps(payload), headers=headers)
    end_time = time.time()
    execution_time = end_time - start_time

    print("\n" + "="*50)
    print(f"📊 حالة الاستجابة (Status Code): {response.status_code}")
    print(f"⏱️ وقت الاستجابة الإجمالي: {execution_time:.3f} ثانية")
    print("="*50)

    # الفحص الأهم: هل الـ CORS هيدر يعود بنجاح؟
    cors_header = response.headers.get('Access-Control-Allow-Origin')
    print(f"🌐 هيدر العبور الـ CORS القادم من السيرفر: {cors_header}")
    if cors_header:
        print("✅ الباك آيند يسمح للفرونت آيند بالوصول وقراءة البيانات بدون مشاكل.")
    else:
        print("❌ خطر: السيرفر لم يرسل Access-Control-Allow-Origin! الفرونت آيند سيفشل في القراءة.")

    print("\n📦 شكل البيانات العائدة (JSON Payload Contract):")
    print(json.dumps(response.json(), indent=4, ensure_ascii=False))

except requests.exceptions.ConnectionError:
    print("\n❌ فشل الاتصال: تأكد من أن سيرفر Django يعمل حالياً على البورت 8000 عبر تنفيذ الأمر: python manage.py runserver")
except Exception as e:
    print(f"\n❌ حدث خطأ غير متوقع: {e}")
