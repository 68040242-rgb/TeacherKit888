from flask import Flask, render_template_string

app = Flask(__name__)

HTML = """
<!DOCTYPE html>
<html lang="th">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TeacherKit | ผู้ช่วยเตรียมการสอน</title>

    <style>
        * {
            box-sizing: border-box;
        }

        body {
            margin: 0;
            font-family: Arial, sans-serif;
            background: #f4f6fb;
            color: #1e293b;
        }

        header {
            background: linear-gradient(135deg, #172554, #3157d5);
            color: white;
            padding: 30px 8%;
        }

        header h1 {
            margin: 0;
            font-size: 32px;
        }

        header p {
            margin-bottom: 0;
            color: #dbeafe;
        }

        nav {
            background: white;
            padding: 16px 8%;
            box-shadow: 0 2px 8px #0000000d;
        }

        nav a {
            text-decoration: none;
            color: #3157d5;
            margin-right: 24px;
            font-weight: bold;
        }

        main {
            max-width: 1100px;
            margin: 35px auto;
            padding: 0 20px;
        }

        .welcome {
            margin-bottom: 25px;
        }

        .welcome h2 {
            font-size: 27px;
            margin-bottom: 8px;
        }

        .welcome p {
            color: #64748b;
        }

        .cards {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 20px;
        }

        .card {
            background: white;
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 5px 20px #00000008;
        }

        .card .icon {
            font-size: 32px;
        }

        .card h3 {
            margin-bottom: 10px;
        }

        .card p {
            color: #64748b;
            line-height: 1.7;
        }

        .button {
            display: inline-block;
            background: #3157d5;
            color: white;
            padding: 12px 18px;
            border-radius: 9px;
            text-decoration: none;
            margin-top: 8px;
        }

        footer {
            text-align: center;
            padding: 30px;
            color: #64748b;
        }

        @media (max-width: 600px) {
            header {
                padding: 25px 6%;
            }

            nav a {
                display: inline-block;
                margin: 5px 12px 5px 0;
            }
        }
    </style>
</head>

<body>

    <header>
        <h1>📚 TeacherKit</h1>
        <p>Smart Teaching Assistant — ผู้ช่วยเตรียมการสอนสำหรับครู</p>
    </header>

    <nav>
        <a href="/">หน้าหลัก</a>
        <a href="#features">เครื่องมือเตรียมสอน</a>
        <a href="#about">เกี่ยวกับเว็บไซต์</a>
    </nav>

    <main>
        <section class="welcome">
            <h2>เตรียมการสอนให้ง่ายขึ้นในที่เดียว ✨</h2>
            <p>
                เครื่องมือช่วยครูวางแผนบทเรียน จัดเตรียมสื่อ
                และจัดระบบงานก่อนเข้าสอน
            </p>
        </section>

        <section class="cards" id="features">

            <div class="card">
                <div class="icon">📝</div>
                <h3>แผนการสอน</h3>
                <p>เตรียมข้อมูลรายวิชา หัวข้อบทเรียน และจุดประสงค์การเรียนรู้</p>
                <a class="button" href="#about">เริ่มต้นใช้งาน</a>
            </div>

            <div class="card">
                <div class="icon">🎯</div>
                <h3>จุดประสงค์การเรียนรู้</h3>
                <p>จัดระบบเป้าหมายการเรียนรู้ให้ชัดเจนและตรวจสอบได้</p>
                <a class="button" href="#about">ดูรายละเอียด</a>
            </div>

            <div class="card">
                <div class="icon">📚</div>
                <h3>สื่อการสอน</h3>
                <p>รวบรวมรายการสื่อ ใบงาน และอุปกรณ์ที่ต้องเตรียม</p>
                <a class="button" href="#about">เตรียมสื่อ</a>
            </div>

            <div class="card">
                <div class="icon">✅</div>
                <h3>เช็กลิสต์ก่อนสอน</h3>
                <p>จัดรายการงานที่ต้องทำก่อนเข้าห้องเรียน</p>
                <a class="button" href="#about">ตรวจสอบงาน</a>
            </div>

        </section>

        <section class="card" id="about" style="margin-top:25px">
            <h3>เกี่ยวกับ TeacherKit</h3>
            <p>
                TeacherKit เป็นแนวคิดเว็บไซต์ที่ออกแบบมาเพื่อช่วยครู
                เตรียมการสอนอย่างเป็นระบบ ตั้งแต่การวางแผนบทเรียน
                ไปจนถึงการเตรียมสื่อและตรวจสอบความพร้อมก่อนเข้าสอน
            </p>
        </section>
    </main>

    <footer>
        TeacherKit © 2026 | ผู้ช่วยเตรียมการสอนสำหรับครู
    </footer>

</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

if __name__ == "__main__":
    app.run(debug=True)
