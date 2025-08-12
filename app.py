import os
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename
from parse_utils import read_chat_from_path, get_emoji_counts
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from datetime import datetime
import collections

UPLOAD_FOLDER = os.path.join('static', 'uploads')
OUTPUT_FOLDER = 'output'
ALLOWED_EXTENSIONS = {'txt'}

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['OUTPUT_FOLDER'] = OUTPUT_FOLDER
app.secret_key = 'cambia-esta-clave'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_plot(fig, path):
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'chatfile' not in request.files:
        flash('No se envió ningún archivo')
        return redirect(request.url)
    file = request.files['chatfile']
    if file.filename == '':
        flash('No se seleccionó archivo')
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

        df = read_chat_from_path(save_path)
        if df.empty or df['datetime'].isna().all():
            flash('No se detectaron mensajes con el formato esperado en el archivo. Revisa el parser.')
            return redirect(url_for('index'))

        # 1) messages per author
        author_counts = df['Author'].value_counts()

        # Definir top_authors para evitar error
        top_authors = author_counts.head(10).index.tolist()

        fig1 = plt.figure(figsize=(10,4))
        ax1 = fig1.add_subplot(111)
        author_counts.plot(kind='bar', ax=ax1)
        ax1.set_title('Número de mensajes por autor')
        ax1.set_xlabel('Autor')
        ax1.set_ylabel('Cantidad de mensajes')
        chart1 = f'author_counts_{filename}.png'
        save_plot(fig1, os.path.join(OUTPUT_FOLDER, chart1))

        # 2) activity by weekday
        weekday_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
        wk = df['weekday'].value_counts().reindex(weekday_order).fillna(0)
        fig2 = plt.figure(figsize=(8,4))
        ax2 = fig2.add_subplot(111)
        wk.plot(kind='bar', ax=ax2)
        ax2.set_title('Actividad por día de la semana')
        ax2.set_xlabel('Día de la semana')
        ax2.set_ylabel('Cantidad de mensajes')
        chart2 = f'weekday_{filename}.png'
        save_plot(fig2, os.path.join(OUTPUT_FOLDER, chart2))

        # 3) emoji counts (pie of top 6)
        emoji_counts = get_emoji_counts(df['Message'])
        top_emojis = collections.Counter(emoji_counts).most_common(6)
        if top_emojis:
            labels = [e for e,c in top_emojis]
            sizes = [c for e,c in top_emojis]
            import matplotlib.font_manager as fm
            emoji_font = fm.FontProperties(fname='C:/Windows/Fonts/seguiemj.ttf')  # Ajusta ruta si usas otro SO
            fig3 = plt.figure(figsize=(6,6))
            ax3 = fig3.add_subplot(111)
            ax3.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
            ax3.set_title('Emojis más usados')
            chart3 = f'emojis_{filename}.png'
            save_plot(fig3, os.path.join(OUTPUT_FOLDER, chart3))
        else:
            chart3 = None

        # 4) multimedia messages per author (top 10)
        media_counts = df[df['is_media']].groupby('Author').size().sort_values(ascending=False).head(10)
        if not media_counts.empty:
            fig4 = plt.figure(figsize=(10,4))
            ax4 = fig4.add_subplot(111)
            media_counts.plot(kind='bar', ax=ax4)
            ax4.set_title('Mensajes multimedia por miembro (top 10)')
            ax4.set_xlabel('Autor')
            ax4.set_ylabel('Cantidad multimedia')
            chart4 = f'media_{filename}.png'
            save_plot(fig4, os.path.join(OUTPUT_FOLDER, chart4))
        else:
            chart4 = None

        # 5) dates with highest activity (top 10)
        date_counts = df['date_only'].value_counts().sort_values(ascending=False).head(10)
        fig5 = plt.figure(figsize=(10,4))
        ax5 = fig5.add_subplot(111)
        date_counts.plot(kind='bar', ax=ax5)
        ax5.set_title('Fechas de mayor actividad (top 10)')
        ax5.set_xlabel('Fecha')
        ax5.set_ylabel('Cantidad de mensajes')
        chart5 = f'dates_{filename}.png'
        save_plot(fig5, os.path.join(OUTPUT_FOLDER, chart5))

        # 6) messages by year
        year_counts = df['year'].value_counts().sort_index()
        fig6 = plt.figure(figsize=(6,3))
        ax6 = fig6.add_subplot(111)
        year_counts.plot(kind='bar', ax=ax6)
        ax6.set_title('Mensajes por año')
        ax6.set_xlabel('Año')
        ax6.set_ylabel('Cantidad')
        chart6 = f'year_{filename}.png'
        save_plot(fig6, os.path.join(OUTPUT_FOLDER, chart6))

        # 7) messages by month (ordered)
        months_order = ['January','February','March','April','May','June','July','August','September','October','November','December']
        month_counts = df['month'].value_counts().reindex(months_order).fillna(0).sort_values(ascending=False)
        fig7 = plt.figure(figsize=(8,4))
        ax7 = fig7.add_subplot(111)
        month_counts.plot(kind='bar', ax=ax7)
        ax7.set_title('Mensajes por mes (ordenado por cantidad)')
        ax7.set_xlabel('Mes')
        ax7.set_ylabel('Cantidad')
        chart7 = f'month_{filename}.png'
        save_plot(fig7, os.path.join(OUTPUT_FOLDER, chart7))

        # 8) hours of activity (top 10)
        hour_counts = df['hour'].value_counts().sort_values(ascending=False).head(10)
        fig8 = plt.figure(figsize=(8,4))
        ax8 = fig8.add_subplot(111)
        hour_counts.plot(kind='bar', ax=ax8)
        ax8.set_title('Horas de mayor actividad (top 10)')
        ax8.set_xlabel('Hora (24h)')
        ax8.set_ylabel('Cantidad')
        chart8 = f'hours_{filename}.png'
        save_plot(fig8, os.path.join(OUTPUT_FOLDER, chart8))

        # prepare last50_by_author
        last50_by_author = {}
        for a in df['Author'].unique():
            last50_by_author[a] = df[df['Author'] == a].tail(50).to_dict('records')

        # prepare emoji summary text
        total_msgs = len(df)
        emoji_summary = None
        if emoji_counts:
            top = collections.Counter(emoji_counts).most_common(3)
            lines = []
            for e,c in top:
                pct = c/total_msgs*100 if total_msgs>0 else 0
                lines.append(f"{e} -> {c} msgs ({pct:.1f}%)")
            emoji_summary = "\n".join(lines)

        charts = {
            'author_counts': chart1,
            'weekday': chart2,
            'emojis': chart3,
            'media': chart4,
            'dates': chart5,
            'year': chart6,
            'month': chart7,
            'hours': chart8
        }

        return render_template('result.html',
                               filename=filename,
                               charts=charts,
                               top_authors=top_authors,
                               author_counts_str=author_counts.to_string(),
                               last50_by_author=last50_by_author,
                               csv_url=url_for('output_file', fname=os.path.basename(os.path.join(OUTPUT_FOLDER, f'chat_table_{filename}.csv'))),
                               emoji_summary=emoji_summary
                               )

    flash('Formato de archivo no permitido (usar .txt)')
    return redirect(url_for('index'))

@app.route('/output/<path:fname>')
def output_file(fname):
    return send_from_directory(app.config['OUTPUT_FOLDER'], fname)

if __name__ == '__main__':
    app.run(debug=True)
