
# Knowledge Management Demo

Testing Knowledge Management Demo in Streamlit using FastAPI.




## Data download

Download the [Documents](https://drive.google.com/drive/folders/1IWTJYPenJ-JSrjnxTaA-p8-6pkrkjifU?usp=drive_link) & [Images](https://drive.google.com/drive/folders/1KZedpRQVC9oZNdv_8ZNyAn_ZrUvveZFM?usp=drive_link) & save them in the cloned repository.




## Installation

Go to the cloned repository & create the virtual enviroment in python
```bash
  cd knowledge-platform-test
```

```bash
  python venv myvenv
```

Activate the virtual enviroment.

```bash
  myvenv\Scripts\activate
```

Install the requirements
```bash
  pip install -r "requirements.txt"
```


    
## Run Locally

After install all the dependencies run the fastapi file..

```bash
  fastapi dev searching_app_fasta.py
```
FastAPI runs on http://127.0.0.1:8000

Run the streamlit file in another terminal....

```bash
  streamlit run searching_app_sl.py
```
Streamlit runs on http://localhost:8501