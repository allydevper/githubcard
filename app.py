import base64
from io import BytesIO
import os
import re
import requests
from flask import Flask, jsonify, render_template, request, send_from_directory
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__, template_folder="templates")

@app.route("/")
def home():
    return render_template("index.html")

@app.route('/image/<filename>')
def get_image(filename):
    return send_from_directory('static/images', filename)

@app.route("/api/generateCard")
def get_generateCard():
    user_proyect = request.args.get('user-proyect')

    def is_valid_repo(text: str) -> bool:
        return bool(re.match(r"^[^/]+/[^/]+$", text))

    if not is_valid_repo(user_proyect):
        return jsonify({"error": "Formato invalido."}), 404

    repo_path = "https://api.github.com/repos/" + user_proyect
    
    response = requests.get(repo_path)
    if response.status_code == 200:
        data = response.json()
        _model = {
            "id": data.get("id"),
            "name": data.get("name"),
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "owner": {
                "login": data["owner"].get("login"),
                "avatar_url": data["owner"].get("avatar_url")
            },
            "stargazers_count": data.get("stargazers_count"),
            "forks_count": data.get("forks_count")
        }

        template_image = Image.open("./assets/mascarav1.png")
        draw = ImageDraw.Draw(template_image)

        # Titulo
        title = _model["full_name"]
        max_length = 34
        if len(title) > max_length:
            title = title[:max_length-1] + "..."
        font = ImageFont.truetype("./assets/Comfortaa.ttf", 28)
        draw.text((288, 55), title, fill="blue", font=font)

        # Summary
        summary = _model["description"]
        font = ImageFont.truetype("./assets/Comfortaa.ttf", 18)
        max_width_size = 580

        def break_text(text, font, max_width):
            words = text.split()
            lines = []
            actual_line = ""

            for palabra in words:
                temp_line = actual_line + " " + palabra if actual_line else palabra
                bbox = draw.textbbox((0, 0), temp_line, font=font)
                text_width = bbox[2] - bbox[0]

                if text_width <= max_width:
                    actual_line = temp_line 
                else:
                    lines.append(actual_line)
                    actual_line = palabra

            if actual_line:
                lines.append(actual_line)

            return lines

        lines = break_text(summary, font, max_width_size)

        x, y = 285, 120 
        line_height = 5

        for line in lines:
            draw.text((x, y), line, fill="black", font=font)
            y += font.size + line_height

        # Star
        star = _model["stargazers_count"]
        if star > 1000:
            star = f"{star / 1000:.1f}K"
        font = ImageFont.truetype("./assets/Comfortaa.ttf", 28)
        draw.text((330, 234), str(star), fill="black", font=font)

        # Fork
        fork = _model["forks_count"]
        if fork > 1000:
            fork = f"{fork / 1000:.1f}K"
        font = ImageFont.truetype("./assets/Comfortaa.ttf", 28)
        draw.text((460, 234), str(fork), fill="black", font=font)

        # Img
        response = requests.get(_model["owner"]["avatar_url"])
        remote_img = Image.open(BytesIO(response.content)).convert("RGBA")
        
        remote_img = remote_img.resize((190, 190)) 
        template_image.paste(remote_img, (50, 50), remote_img)

        buffer = BytesIO()
        template_image.save(buffer, format="PNG")
        imagen_base64 = base64.b64encode(buffer.getvalue()).decode()
        return jsonify({"image": imagen_base64})
    else:
        return jsonify({"error": "No se pudo obtener la información del repositorio."}), 404

if __name__ == "__main__":
    print(f"Directorio de trabajo actual: {os.getcwd()}")
    print(f"Archivos en templates/: {os.listdir('templates')}")
    app.run(debug=True)