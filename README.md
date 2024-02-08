# Supervised-Sleep
Sleep quality predictions using supervised machine learning.

This project is intended as a demonstration and exploring in training machine learning predictive models on Oura Ring exported user data. The ground truth target variable is the sleep score assigned to each day from the exported data. Along with the goal of creating a well-fit model for this problem, both regression and classification models will be used in this project, exploring the efficacy of turning the discrete sleep scores into ordinal categorical variables.

Since the data collection period is currently limited, this project has been made with the goal of handling continued data uploads (all data cleaning/analysis will be generalized for continuous new data).

*This project is licensed under the terms of the MIT License, but is intended for private use only.*

*If you fork or use any part of this project please attribute Cody Hill as the creator of this work.*

---

**Environment Information / Dependencies:**

Python version: 3.11.7 (main, Dec  4 2023, 18:10:11) [Clang 15.0.0 (clang-1500.1.0.2.5)]\
module 'numpy'  using version: 1.26.3\
module 'pandas'  using version: 2.1.4\
module 'sklearn'  using version: 1.3.2\
module 'scipy'  using version: 1.11.4\
module 'statsmodels.api'  using version: 0.14.1\
module 'matplotlib'  using version: 3.8.2\
module 'seaborn'  using version: 0.13.2

**Parameters you might be interested in changing:**
- Train Test Split Section:
  - `rand_state` = 87654321
  - `test_ratio` = 0.2
  - `bin_type` = 'score_bin_custom'