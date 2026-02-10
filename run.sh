#!/bin/bash

echo "🔥 Starting your Django project…"

# create virtual environment if not exists
if [ ! -d "venv" ]; then
    echo "✨ Creating virtual environment…"
    python3 -m venv venv
fi

# activate venv
source venv/bin/activate

# upgrade pip
echo "⬆️  Upgrading pip…"
pip install --upgrade pip

# install dependencies
if [ -f "requirements.txt" ]; then
    echo "📦 Installing dependencies…"
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found, skipping install"
fi

# run migrations
echo "🛠️ Running migrations…"
python manage.py makemigrations
# run migrations
echo "🛠️ Running migrate..."
python manage.py migrate

# collect static files (optional)
# python manage.py collectstatic --noinput

# runserver
echo "🚀 Running server on 0.0.0.0:8471"
python manage.py runserver 0.0.0.0:8471
