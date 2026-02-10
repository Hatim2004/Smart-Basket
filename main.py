import cv2
import requests
import numpy as np
import base64
import time

# --- CONFIGURATION ---
ROBOFLOW_API_URL = "https://detect.roboflow.com"
ROBOFLOW_KEY = ""
MODEL_ID = "basket-hvfwb/3"

ESP32_IP = "http://192.168.100.230/capture"
SERVER_API = "http://localhost:8000/api/add"

print("Starting Detection System...")

while True:
    try:
        # 1. Get Image from ESP32
        img_resp = requests.get(ESP32_IP, timeout=3)
        if img_resp.status_code != 200:
            print("Failed to get image from ESP32")
            continue

        img_arr = np.array(bytearray(img_resp.content), dtype=np.uint8)
        frame = cv2.imdecode(img_arr, -1)

        if frame is None:
            print("Failed to decode image")
            continue

        # 2. Prepare Image for Roboflow API (Manual POST request)
        # Encode frame to jpg
        retval, buffer = cv2.imencode('.jpg', frame)
        img_str = base64.b64encode(buffer).decode("utf-8")

        # Construct URL
        upload_url = f"{ROBOFLOW_API_URL}/{MODEL_ID}?api_key={ROBOFLOW_KEY}"

        # Send POST request
        response = requests.post(
            upload_url,
            data=img_str,
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )

        results = response.json()

        # 3. Process Predictions
        if 'predictions' in results:
            for p in results['predictions']:
                item_name = p['class']
                confidence = p['confidence']

                # --- LOGIC START ---
                is_valid = False

                # RULE 1: If it is Noodles, allow 60% (0.60) or higher
                if item_name == "Noodles" and confidence >= 0.60:
                    is_valid = True

                # RULE 2: For everything else, require 80% (0.80) or higher
                elif confidence >= 0.80:
                    is_valid = True

                # Only proceed if one of the rules was met
                if is_valid:
                    # Bounding box logic (Roboflow returns center x,y and width,height)
                    x = int(p['x'])
                    y = int(p['y'])
                    w = int(p['width'])
                    h = int(p['height'])

                    x1 = int(x - w / 2)
                    y1 = int(y - h / 2)
                    x2 = int(x + w / 2)
                    y2 = int(y + h / 2)

                    # Draw Green Box
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)

                    # Label text
                    label = f"{item_name} {confidence:.2f}"
                    cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    print(f"Found: {item_name} ({confidence:.2f})")

                    # Send to Website Server
                    try:
                        requests.post(SERVER_API, json={"name": item_name})
                    except Exception as e:
                        print(f"Server API Error: {e}")
                # --- LOGIC END ---

        # 4. Show Video Feed
        cv2.imshow("ESP32 AI View", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(1)

cv2.destroyAllWindows()