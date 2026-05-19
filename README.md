# ScholarshipRecommendation Project Report

 

## Chapter 1: Introduction

### 1.1 Introduction to the Problem Domain
Many students miss scholarships because it is difficult to understand eligibility rules, income limits, category rules, education requirements, and application details from different sources. Scholarship portals usually contain large lists, but users still need help finding the right scholarship quickly.

This project solves that problem by combining a web interface, a backend API, and machine learning models to recommend scholarships based on a student profile. The system helps a user:
- find matching scholarships,
- check eligibility,
- estimate success probability,
- and save useful recommendations.

### 1.2 Aim / Statement of the Problem
The aim of the project is to build a smart scholarship recommendation system that can suggest suitable scholarships to a student using profile data such as marks, income, category, gender, disability, education level, and state.

### 1.3 Objectives of the Project Work
- Collect scholarship data from available spreadsheets and structured files.
- Build a user-friendly frontend for entering profile details and viewing recommendations.
- Connect the frontend to a backend service that performs recommendation and eligibility analysis.
- Train machine learning models for ranking, eligibility prediction, and success prediction.
- Measure model quality using accuracy, confusion matrix, error rate, and related metrics.
- Provide a simple and practical system that can be used by students without technical knowledge.

### 1.4 Applications
- Scholarship search and recommendation for students.
- Eligibility checking before application.
- Scholarship guidance for college administration or counselors.
- Data-driven decision support for education portals.

---

## Chapter 2: Tools and Technology Used

### 2.1 Project Theme
The project theme is **AI-based scholarship recommendation and eligibility prediction**. It combines web development, backend APIs, authentication, and machine learning.

### 2.2 Frontend Technologies
The frontend is built using:
- **HTML5** for page structure.
- **CSS3** for layout, animation, color scheme, and responsive design.
- **Vanilla JavaScript** for API calls, rendering cards, filtering results, and live updates.
- **Google Fonts** (`Poppins`, `Inter`) for modern typography.
- **SVG icons** for scalable visuals.

Why this frontend stack was used:
- It is lightweight and easy to run in a local environment.
- It does not require a heavy framework such as React or Angular.
- It works well with static hosting and PHP/Flask integration.
- It is easier to deploy with XAMPP and simple server setups.

Why not a heavier frontend framework:
- The project is small to medium in size.
- The current UI needs fast loading and simple integration.
- Plain JavaScript is enough for API calls and card rendering.

### 2.3 Backend Technologies
The project actually uses **two backend layers**:

#### A. Flask recommendation backend
The Flask backend in `backend/app.py` is responsible for:
- loading scholarship datasets,
- loading trained ML models,
- computing recommendations,
- returning JSON responses to the frontend,
- and serving frontend assets when needed.

Technologies used here:
- **Python 3**
- **Flask**
- **Flask-CORS** for cross-origin requests
- **pandas** and **numpy** for data handling
- **scikit-learn** for ML inference and similarity scoring
- **pickle** for loading saved models
- **SQLite** for local auth storage in the Flask app

#### B. PHP authentication layer
The `php/` folder provides:
- login,
- registration,
- profile storage,
- dashboard display,
- session handling,
- and MySQL-based persistence.

This is used for user authentication and saved profile management.

Why backend is split this way:
- Flask is better suited for ML inference and Python models.
- PHP is already used for simple login/register/dashboard workflows.
- The separation keeps recommendation logic and user authentication independent.

### 2.4 Machine Learning Technologies
The ML part uses:
- **Logistic Regression**
- **Random Forest Classifier**
- **Random Forest Regressor**
- **TF–IDF Vectorizer**
- **StandardScaler**
- **OneHotEncoder**
- **ColumnTransformer**
- **train_test_split** and evaluation metrics from scikit-learn

### 2.5 Data Sources
Important datasets used by the project include:
- `ml/structured_real_scholarships.csv`
- `data/scholarship_50000_dataset.xlsx`
- other `.xlsx` files inside `data/` used during dataset rebuilding

### 2.6 Why These Technologies Were Chosen
- **HTML/CSS/JS**: fast, simple, and suitable for a clean responsive UI.
- **Flask**: easy to connect Python ML models with a web API.
- **PHP/MySQL**: convenient for basic authentication and profile management.
- **scikit-learn**: reliable for classical ML algorithms and preprocessing.
- **TF–IDF**: good for matching scholarship descriptions/attributes.
- **Random Forest**: handles mixed feature types and non-linear relationships well.
- **Logistic Regression**: simple, stable, and interpretable for eligibility classification.

### 2.7 Why Other Options Were Not Chosen
- **React/Angular** were not necessary because the UI logic is moderate and the current app can be handled with plain JS.
- **Deep learning models** were not needed because the data is mostly tabular and rule-driven.
- **MongoDB** was not required because the current backend authentication and data flow work with SQLite/MySQL.
- **SVM / XGBoost** could have been used, but Random Forest and Logistic Regression are easier to explain, tune, and maintain for this project.

---

## Chapter 3: System Design and Implementation

### 3.1 Overall Architecture
The system follows a simple three-part architecture:

1. **Frontend**
   - collects user profile details,
   - displays scholarship cards,
   - shows saved scholarships and live feed.

2. **Backend**
   - receives the student profile,
   - loads scholarship data,
   - applies ML or scoring logic,
   - returns ranked recommendations.

3. **ML Models / Data Layer**
   - stores trained models and structured datasets,
   - provides the recommendation intelligence.

### 3.2 Frontend Implementation
The frontend in `frontend/` contains:
- `index.html` for layout,
- `styles.css` for the design system,
- `script.js` for interaction and API communication,
- other pages like login/register/welcome screens.

How the frontend works:
- User enters marks, income, category, gender, disability, state, and education level.
- JavaScript sends this data using `fetch()` to the backend endpoint.
- Results come back as JSON.
- The UI renders recommendation cards dynamically.

Important frontend features:
- responsive card layout,
- result counters,
- live ticker,
- save/unsave feature,
- accuracy / response time / error rate display,
- session-based login UI updates.

### 3.3 Backend Connection
The frontend connects to backend services by HTTP requests.

Main connections seen in the code:
- `frontend/script.js` calls `/api/recommend` for scholarship recommendations.
- `frontend/script.js` calls `/api/dataset-preview` to show live ticker names.
- `frontend/index.html` uses PHP endpoints like `../php/api_me.php` and `../php/logout.php` for authentication state.

So the system is connected like this:
- **Frontend UI** → sends profile data
- **Flask API** → returns recommendation results
- **PHP session API** → manages login/logout and saved user profile
- **ML models** → provide scoring/ranking/eligibility logic

### 3.4 Database / Storage Design
- The Flask backend uses a local SQLite auth file for internal auth storage.
- The PHP layer uses MySQL with PDO connection helpers.
- Trained ML artifacts are saved as `.pkl` files inside `ml/`.
- Structured scholarship records are stored in CSV format for faster loading.

### 3.5 ML Implementation Flow
The implementation happens in stages:
1. Load raw spreadsheet data from `data/`.
2. Clean and normalize scholarship fields.
3. Build training features.
4. Split data into train and test sets.
5. Train models.
6. Evaluate using metrics.
7. Save models with `pickle`.
8. Load them in the Flask backend for inference.

---

### 3.6 Machine Learning Algorithms Used

#### A. Logistic Regression
Used in `ml/train_eligibility_model.py`.

How it works:
- Takes numeric features such as marks difference, income margin, and category/gender/disability match.
- Learns a boundary between eligible and not eligible examples.
- Outputs probability-like binary classification.

Why this algorithm:
- simple and fast,
- works well for binary output,
- easy to explain in a project report.

#### B. TF–IDF Vectorizer
Used in `ml/train_rank_model.py`.

How it works:
- Converts scholarship attributes into a text-like feature string.
- Assigns weight to important terms.
- Helps compare similarity between scholarships and user profile patterns.

Why this algorithm:
- useful for ranking/matching,
- compact and efficient,
- works well when scholarship attributes are treated like keywords.

#### C. Random Forest Classifier
Used in `ml/train_success_model.py` and `ml/train_eligibility_predictor.py`.

How it works:
- Builds many decision trees.
- Each tree votes for the output class.
- Final prediction is the majority vote.

Why this algorithm:
- handles mixed feature types,
- captures non-linear rules,
- robust to noise,
- often better than a single decision tree.

#### D. Random Forest Regressor
Used in `ml/train_eligibility_predictor.py`.

How it works:
- Similar to Random Forest Classifier,
- but predicts a continuous value,
- here used for percentage/score estimation.

#### E. Preprocessing Methods
- **StandardScaler**: normalizes numeric features so the model sees them on a similar scale.
- **OneHotEncoder**: converts category labels into numeric columns.
- **ColumnTransformer**: applies different preprocessing steps to different column types.

---

### 3.7 Dataset Preparation and Normalization
Data preparation is one of the most important parts of the project.

Steps used:
1. Read the source `.xlsx` or `.csv` files.
2. Convert column names to a common format.
3. Fill missing values.
4. Normalize values like education level, category, gender, and disability.
5. Convert income and marks into numeric values.
6. Build clean training features.

Why normalization is needed:
- to avoid inconsistent labels like `UG`, `ug`, `degree`, `bachelor`,
- to keep the model from treating same meanings as different values,
- to improve consistency and prediction quality.

---

### 3.8 Training Process

#### Eligibility Model Training
File: `ml/train_eligibility_model.py`

Process:
1. Load scholarship CSV.
2. Fill missing columns with defaults.
3. Generate synthetic student examples for each scholarship.
4. Use a rule-based function to label examples as eligible or not eligible.
5. Split into train and test sets.
6. Scale features using `StandardScaler`.
7. Train `LogisticRegression`.
8. Save the classifier and scaler.

#### Ranking Model Training
File: `ml/train_rank_model.py`

Process:
1. Rebuild structured scholarship data from all `.xlsx` files in `data/`.
2. Normalize fields like gender, category, education, and state.
3. Convert each scholarship into a compact feature text.
4. Apply `TfidfVectorizer` with unigram and bigram features.
5. Save the vectorizer, feature matrix, and scholarship names.

#### Success Model Training
File: `ml/train_success_model.py`

Process:
1. Load `scholarship_50000_dataset.xlsx`.
2. Create a `selected` label using scholarship rules.
3. Encode categorical values.
4. Train `RandomForestClassifier`.
5. Evaluate with accuracy, classification report, and confusion matrix.
6. Save the full pipeline.

#### Full Eligibility + Percentage Predictor Training
File: `ml/train_eligibility_predictor.py`

Process:
1. Load the large dataset.
2. Explore missing values and data types.
3. Build features from numeric and categorical columns.
4. Create eligibility and percentage targets.
5. Split train/test data.
6. Scale features.
7. Train `RandomForestClassifier` for eligibility.
8. Train `RandomForestRegressor` for percentage prediction.
9. Save classifier, regressor, scaler, and label encoders.

---

## Chapter 4: System Testing and Results Analysis

### 4.1 Testing Approach
The project can be tested at three levels:
- **Frontend testing**: check form input, card rendering, and UI interaction.
- **Backend testing**: check API responses, JSON format, and connection to the frontend.
- **ML testing**: evaluate prediction quality on train/test data.

### 4.2 What Was Tested
- User profile submission.
- API connectivity between frontend and backend.
- Scholarship ranking output.
- Eligibility prediction output.
- Success probability and chance level display.
- Login/logout flow.
- Save/unsave scholarship behavior.

### 4.3 Metrics Used
The ML scripts use the following metrics:
- **Accuracy** — how many predictions were correct.
- **Precision** — how many predicted positives were correct.
- **Recall** — how many actual positives were found.
- **F1-score** — balance between precision and recall.
- **Confusion Matrix** — counts of true/false predictions.
- **RMSE / MAE / R²** — used for the regression output.

### 4.4 Error Rate
Error rate can be understood as:
$$
	ext{Error Rate} = 1 - \text{Accuracy}
$$

If accuracy is 92%, the error rate is 8%.

### 4.5 Accuracy and Output Discussion
The actual output depends on:
- dataset quality,
- preprocessing quality,
- feature design,
- and how well the labels represent real scholarship eligibility.

Expected output from the system:
- a ranked list of scholarships,
- eligibility status,
- success probability,
- chance level,
- and model metrics shown on the card.

### 4.6 Redundancy / Overfitting Discussion
Redundancy here means repeated or unnecessary information/features in the training data.

How the project reduces redundancy:
- deduplicating scholarship names,
- normalizing repeated categories and education levels,
- selecting only relevant features,
- using train/test split,
- and keeping the model simple enough to avoid overfitting.

Why this matters:
- fewer duplicate patterns,
- better generalization,
- less noisy predictions.

### 4.7 Normalization Discussion
Normalization is used in two ways:
- **Text/category normalization**: `UG`, `degree`, `bachelor`, `undergraduate` become one consistent label.
- **Numeric scaling**: income and marks are scaled where needed.

This improves stability and makes the model easier to train.

### 4.8 Result Analysis
The project is designed to show that scholarship recommendation can be improved when:
- a structured dataset is cleaned properly,
- rule-based features are combined with ML,
- and the frontend is connected to a reliable backend.

Even if some data is rule-generated or synthetic, the system still demonstrates a full end-to-end recommendation pipeline.

---

## Chapter 5: Conclusion and Future Work

### 5.1 Conclusion
The ScholarshipRecommendation project provides a complete scholarship guidance system by combining web development, backend APIs, authentication, and machine learning. It helps users find scholarships faster, understand eligibility, and estimate their chance of success.

### 5.2 Future Work
- Replace synthetic labels with more real-world labeled scholarship outcomes.
- Add stronger ranking using semantic search or embeddings.
- Move authentication to a single backend technology for cleaner architecture.
- Add user-specific recommendations from historical behavior.
- Improve explainability by showing why a scholarship matched a profile.
- Add deployment support for cloud hosting.
- Add automated testing for frontend and backend APIs.

---

## Quick Project Summary

- **Frontend**: HTML, CSS, JavaScript, Google Fonts, SVG.
- **Backend**: Flask API, PHP/MySQL auth, SQLite auth storage in Flask.
- **ML**: Logistic Regression, Random Forest, TF–IDF, StandardScaler, OneHotEncoder.
- **Data**: CSV and Excel scholarship datasets.
- **Core flow**: user profile → backend API → ML model scoring → ranked scholarship recommendations.

---
 


## Detailed Addendum

This section is added at the bottom only, so the existing report remains unchanged. It gives a more direct explanation of the project in simple language.

### Project Theme
The project theme is **scholarship recommendation and eligibility prediction using machine learning**. The idea is to help students quickly find scholarships that match their profile instead of manually checking many websites and documents.

### What the Frontend Uses
The frontend uses:
- **HTML** for structure,
- **CSS** for design and responsive layout,
- **JavaScript** for dynamic behavior and API calls,
- **Google Fonts** for better appearance,
- **SVG icons** for scalable visuals.

Why this frontend was used:
- It is simple to understand and easy to maintain.
- It loads fast and works well in a browser without extra frameworks.
- It is enough for form input, result cards, and live updates.

Why not another frontend framework:
- React or Angular would add extra complexity for this project size.
- The current project does not need advanced component architecture.
- Vanilla JavaScript is enough for sending requests and rendering results.

### How the Frontend Connects to the Backend
The frontend connects to the backend using HTTP requests.

Main connections:
- `frontend/script.js` sends the student profile to `/api/recommend`.
- The backend returns scholarship results in JSON format.
- The frontend reads the JSON and shows scholarship cards.
- PHP endpoints like `api_me.php` and `logout.php` manage login state.

So the flow is:
1. User fills the form.
2. JavaScript sends data to backend.
3. Backend runs model-based scoring.
4. Backend sends results back.
5. Frontend displays the results.

### Tech Stack Used
- **Frontend**: HTML, CSS, JavaScript, Google Fonts, SVG.
- **Backend**: Flask, Python, Flask-CORS, pandas, numpy, scikit-learn, pickle.
- **Authentication layer**: PHP, MySQL, sessions.
- **Data storage**: CSV, Excel, SQLite, MySQL.
- **ML tooling**: Logistic Regression, Random Forest, TF–IDF, StandardScaler, OneHotEncoder, ColumnTransformer.

### ML Part: Which Algorithms Were Used
The project uses multiple machine learning approaches because the problem has more than one part.

#### 1. Logistic Regression
Used for eligibility classification in `ml/train_eligibility_model.py`.

Why this algorithm:
- It is simple and efficient.
- It works well when the output is just two classes: eligible or not eligible.
- It is easy to explain in a report.

How it works:
- It takes input features such as marks difference, income margin, category match, gender match, and disability match.
- It learns a mathematical boundary between eligible and not eligible cases.
- It returns a binary prediction.

#### 2. TF–IDF Vectorizer
Used in `ml/train_rank_model.py`.

Why this algorithm:
- It helps compare scholarship descriptions and attributes.
- It is useful for ranking and similarity matching.
- It works well when scholarship details are treated as text-like features.

How it works:
- Each scholarship is converted into a feature string such as category, gender, education, income bucket, and state.
- TF–IDF gives more weight to important terms.
- Similar scholarships get similar vector values.

#### 3. Random Forest Classifier
Used in `ml/train_success_model.py` and `ml/train_eligibility_predictor.py`.

Why this algorithm:
- It handles mixed data types well.
- It can capture non-linear decision rules.
- It usually gives stable results on tabular data.

How it works:
- It creates many decision trees.
- Each tree makes a prediction.
- The final output is based on majority voting.

#### 4. Random Forest Regressor
Used in `ml/train_eligibility_predictor.py` for percentage prediction.

How it works:
- It is similar to the classifier version.
- Instead of voting for a class, it predicts a numeric value.
- Here it predicts an estimated success/percentage score.

### Entire Process of Training the Model
The training flow is as follows:
1. Collect scholarship data from `.xlsx` and `.csv` files.
2. Clean the data and fix missing values.
3. Normalize labels like category, gender, education level, and disability.
4. Build features from scholarship rules and student profile conditions.
5. Split the data into training and testing sets.
6. Train the ML model.
7. Evaluate the model using accuracy and other metrics.
8. Save the trained model with `pickle`.
9. Load the model in the backend for live recommendations.

### Accuracy, Output, and Error Rate
The scripts evaluate model quality using standard metrics.

Common metrics used:
- **Accuracy**: percentage of correct predictions.
- **Precision**: how many predicted eligible cases were actually eligible.
- **Recall**: how many actual eligible cases were found.
- **F1-score**: balance between precision and recall.
- **Confusion matrix**: shows correct and incorrect predictions.
- **RMSE / MAE / R²**: used for the percentage prediction output.

Error rate is the opposite of accuracy:
$$
	ext{Error Rate} = 1 - \text{Accuracy}
$$

If accuracy is high, the error rate becomes low.

### Redundancy and Normalization
#### Redundancy
Redundancy means repeated or unnecessary data. The project reduces redundancy by:
- removing duplicate scholarship names,
- using only important features,
- cleaning repeated labels,
- and splitting train/test data properly.

#### Normalization
Normalization means making values consistent.
Examples:
- `UG`, `degree`, and `bachelor` are treated as the same level.
- `male`, `M`, and `boy` can be normalized to one standard label.
- numeric values like income and marks are converted into proper numbers.

Normalization helps the model learn better and reduces confusion in training.

### Output of the System
The system output is a ranked list of scholarships with details such as:
- scholarship name,
- match score,
- eligibility status,
- success probability,
- chance level,
- amount,
- and additional model metrics.

### Why This Project Works Well
- It combines rule-based logic with ML scoring.
- It uses a clear frontend and backend flow.
- It gives practical outputs that a student can actually use.
- It is modular, so each part can be improved later.

### Short Final Explanation
This project takes a student profile, compares it with scholarship rules, applies machine learning models, and then shows the best matching scholarships along with predicted eligibility and success scores. The whole flow is designed to save time, reduce manual searching, and make scholarship discovery easier.

### Project-Specific Answers for Training, Testing, Accuracy, and Efficiency
#### How the data was trained and tested in this project
- In `ml/train_eligibility_model.py`, the scholarship CSV is loaded from `ml/structured_real_scholarships.csv`.
- The script creates **synthetic student examples** for every scholarship using the scholarship rules already stored in the dataset.
- Each example is labeled by the `rule_based_eligible()` function, which checks marks, income, category, gender, and disability conditions.
- The generated feature matrix is split with `train_test_split(test_size=0.2, random_state=42)`, so **80% is training data and 20% is testing data**.
- The features are scaled with `StandardScaler`, and then the model is trained.
- In `ml/train_success_model.py`, the larger file `data/scholarship_50000_dataset.xlsx` is loaded, a `selected` label is created from scholarship rules, and the model is also split into train/test sets with **80/20**.
- In `ml/train_eligibility_predictor.py`, the project builds feature columns from the dataset, splits them with `train_test_split(test_size=0.2, random_state=42)`, scales the data, and trains both a classifier and a regressor.

#### How accuracy and error rate are calculated in this project
- In `ml/train_eligibility_model.py`, test accuracy is calculated using `clf.score(X_test_scaled, y_test)` after scaling the test features.
- In `ml/train_success_model.py`, accuracy is calculated with `accuracy_score(y_test, preds)`.
- In `ml/train_eligibility_predictor.py`, the project prints **accuracy, precision, recall, F1-score, confusion matrix, RMSE, MAE, and R²**.
- The error rate used in the project is the complement of accuracy:
$$
	ext{Error Rate} = 100 - \text{Accuracy Percentage}
$$
- So if the test accuracy is 92%, the error rate is 8%.

#### How much percentage efficient the project is
- The project does **not** have one permanent efficiency percentage, because the number changes with the dataset and the trained model.
- The efficiency percentage of the deployed model is the **test accuracy** printed by the training script.
- For the backend UI, the card shows API metrics such as `accuracy_percent`, `error_rate_percent`, and `last_response_time_ms` returned by the Flask backend.
- In other words, the project efficiency is measured by the model’s test accuracy and related scores, not by a fixed hardcoded number.

#### Exact project meaning of the metrics
- **Accuracy** = how many test predictions were correct for your scholarship dataset.
- **Error rate** = how many test predictions were wrong.
- **Efficiency** = the same test performance shown as a percentage in the model output or API metrics.
- **Regression quality** = how close the predicted success percentage is to the expected percentage, measured by RMSE, MAE, and R².


