from api import create_api

api = create_api(allow_cors=True)

# uvicorn.run(app, host="0.0.0.0", port=8000)
