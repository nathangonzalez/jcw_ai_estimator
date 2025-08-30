from fastapi import FastAPI

app = FastAPI(title='Coastal BIM AI API')

@app.get('/health')
def health(): return {'ok': True}
