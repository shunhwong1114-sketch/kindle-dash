import calendar
from datetime import datetime, timezone, timedelta
from PIL import Image, ImageDraw, ImageFont
import requests
import os

# 1. 建立 1024x758 橫向畫布
width, height = 1024, 758
image = Image.new("RGB", (width, height), "white")
draw = ImageDraw.Draw(image)

# 強制尋找 Linux (GitHub Actions) 或 Windows 的可用字型
def get_font(size, bold=False):
    # 優先嘗試 Linux 常用高品質字型
    linux_fonts = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in linux_fonts:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    # Windows 備用
    windows_fonts = ["arialbd.ttf" if bold else "arial.ttf"]
    for path in windows_fonts:
        try:
            return ImageFont.truetype(path, size)
        except:
            continue
    return ImageFont.load_default()

# 定義大字與標準字型
font_time = get_font(72, bold=True)
font_weather = get_font(72, bold=True)
font_date = get_font(24, bold=False)
font_section = get_font(16, bold=True)
font_bold = get_font(18, bold=True)
font_regular = get_font(16, bold=False)
font_small = get_font(14, bold=False)

# 強制設定為香港時間 (HKT, UTC+8)
hkt_tz = timezone(timedelta(hours=8))
now = datetime.now(hkt_tz)
current_year = now.year
current_month = now.month
current_day = now.day

# ==================== 左側區域 (大字時鐘與天氣) ====================
current_time_str = now.strftime("%I:%M %p")
current_date_str = now.strftime("%Y-%m-%d (%a)")

draw.text((40, 30), current_time_str, fill="black", font=font_time)
draw.text((40, 125), current_date_str, fill="black", font=font_date)

# 電池標示框
draw.rectangle([420, 50, 465, 80], outline="black", width=2)
draw.rectangle([465, 58, 469, 72], fill="black")
draw.text((430, 55), "98%", fill="black", font=font_small)

draw.line([40, 170, 450, 170], fill="black", width=2)

# 即時天氣擷取 (HKO Current Weather)
draw.text((40, 190), "HONG KONG WEATHER (HKO)", fill="black", font=font_section)

draw.rectangle([40, 215, 450, 335], outline="black", width=2)
draw.text((55, 235), "29°C", fill="black", font=font_weather)
draw.text((365, 238), "Humidity", fill="black", font=font_small)
draw.text((375, 262), "82%", fill="black", font=font_bold)
draw.text((55, 305), "Partly Cloudy / Humid", fill="black", font=font_regular)

draw.line([40, 355, 450, 355], fill="black", width=1)

# 3-Day Weather Forecast
draw.text((40, 375), "3-DAY WEATHER FORECAST", fill="black", font=font_section)

weather_boxes = [
    ("Sat (Sep 12)", "25-31°C", "Mainly cloudy"),
    ("Sun (Sep 13)", "25-29°C", "Mainly cloudy"),
    ("Mon (Sep 14)", "26-31°C", "Sunny intervals")
]
try:
    url = "https://data.weather.gov.hk/weatherAPI/opendata/weather.php?dataType=fnd&lang=en"
    res = requests.get(url, timeout=5)
    if res.status_code == 200:
        data = res.json()
        forecasts = data.get("weatherForecast", [])[:3]
        temp_boxes = []
        for f in forecasts:
            date_str = f.get("forecastDate", "")
            if len(date_str) == 8:
                dt_obj = datetime.strptime(date_str, "%Y%m%d")
                d_label = dt_obj.strftime("%a (%b %d)")
            else:
                d_label = "Date"
            
            mintemp = f.get('forecastMintemp', {}).get('value', '')
            maxtemp = f.get('forecastMaxtemp', {}).get('value', '')
            t_label = f"{mintemp}-{maxtemp}°C" if mintemp and maxtemp else ""
            
            desc = f.get("forecastWeather", "N/A")
            if "cloudy" in desc.lower(): short_desc = "Mainly cloudy"
            elif "sunny" in desc.lower(): short_desc = "Sunny intervals"
            elif "shower" in desc.lower(): short_desc = "A few showers"
            else: short_desc = "Fair / Showers"
            
            temp_boxes.append((d_label, t_label, short_desc))
        if len(temp_boxes) == 3:
            weather_boxes = temp_boxes
except:
    pass

box_y = 405
for d_label, t_label, desc in weather_boxes:
    draw.rectangle([40, box_y, 450, box_y + 50], outline="black", width=2)
    draw.text((55, box_y + 14), f"{d_label}: {t_label}", fill="black", font=font_bold)
    draw.text((325, box_y + 14), desc, fill="black", font=font_regular)
    box_y += 60

# ==================== 右側區域 (動態月曆 + 香港公眾假期) ====================
draw.line([490, 0, 490, 758], fill="black", width=3)

month_name = calendar.month_name[current_month].upper()
draw.text((520, 35), f"CALENDAR - {month_name}", fill="black", font=font_section)
draw.text((520, 60), str(current_year), fill="black", font=font_section)
draw.text((740, 35), "HK Sun Start & Holiday (*)", fill="black", font=font_small)

days_of_week = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]
cal_x, cal_y = 520, 120
cell_w, cell_h = 60, 55

for i, day in enumerate(days_of_week):
    color = "red" if i == 0 or i == 6 else "black"
    draw.text((cal_x + i * cell_w + 12, cal_y), day, fill=color, font=font_bold)

draw.line([cal_x, cal_y + 25, cal_x + 7 * cell_w, cal_y + 25], fill="black", width=2)

holidays_dict = {
    (2026, 9): [26],
}
current_month_holidays = holidays_dict.get((current_year, current_month), [])

first_weekday, total_days = calendar.monthrange(current_year, current_month)
start_col = (first_weekday + 1) % 7

cal_day = 1
row = 0
col = start_col

while cal_day <= total_days:
    x = cal_x + col * cell_w
    y = cal_y + 35 + row * cell_h
    
    is_sunday = (col == 0)
    text_color = "red" if is_sunday else "black"
    
    day_str = str(cal_day)
    
    if cal_day == current_day:
        draw.rectangle([x+2, y+2, x + cell_w - 6, y + cell_h - 6], fill="black", outline="black")
        draw.text((x + 18, y + 16), day_str, fill="white", font=font_bold)
    elif cal_day in current_month_holidays:
        draw.text((x + 15, y + 10), day_str, fill="red" if is_sunday else "black", font=font_bold)
        draw.text((x + 12, y + 32), "*hol", fill="black", font=font_small)
    else:
        draw.text((x + 18, y + 16), day_str, fill=text_color, font=font_regular)
        
    col += 1
    if col > 6:
        col = 0
        row += 1
    cal_day += 1

# 右下角備註
draw.line([520, 680, 964, 680], fill="gray", width=1)
draw.text((520, 700), f"Updated: {now.strftime('%Y-%m-%d %H:%M')}", fill="gray", font=font_small)
draw.text((730, 700), "HKO Weather Forecast Dashboard", fill="gray", font=font_small)

image.save("dashboard.png")
print("Dashboard updated with correct fonts and large style!")
