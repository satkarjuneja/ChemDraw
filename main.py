from backend import app
from vercel import VercelHandler

handler = VercelHandler(app)

def main(request):
    return handler(request)
