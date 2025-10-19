from flask import Blueprint, render_template_string

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def home():
    html = """
    <html>
        <head>
            <title>MeteoSphere</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    text-align: center;
                    margin-top: 15%;
                    background: linear-gradient(135deg, #74ABE2, #5563DE);
                    color: white;
                }
                h1 {
                    font-size: 3em;
                }
                p {
                    font-size: 1.3em;
                }
                a {
                    color: #fff;
                    background: rgba(255,255,255,0.2);
                    padding: 10px 20px;
                    border-radius: 10px;
                    text-decoration: none;
                    transition: 0.3s;
                }
                a:hover {
                    background: rgba(255,255,255,0.4);
                }
            </style>
        </head>
        <body>
            <h1>🌤️ Welcome to MeteoSphere</h1>
            <p>Your intelligent weather assistant.</p>
            <a href="/api/docs">Go to API Docs</a>
        </body>
    </html>
    """
    return render_template_string(html)
