# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a content recommendation system project for "My Content" that implements a personalized article recommendation engine. The system analyzes user interaction data to recommend 5 relevant articles per user based on their preferences and reading history.

## Data Structure

The project works with the following data files:
- `data/articles_metadata.csv`: Article metadata (364,047 articles) with columns: article_id, category_id, created_at_ts, publisher_id, words_count
- `data/articles_embeddings.pickle`: Pre-calculated 250-dimensional embeddings for all articles (numpy arrays)
- `data/clicks/`: Directory containing 385 hourly click data files (clicks_hour_000.csv to clicks_hour_384.csv)
- `data/clicks_sample.csv`: Sample of click interactions for quick testing

## Development Commands

### Running the Notebook
```bash
jupyter notebook my_content_recommendation_system.ipynb
```

### Python Environment
This project uses standard data science libraries. Key dependencies include:
- pandas, numpy for data manipulation
- scikit-learn for ML algorithms and metrics
- matplotlib, seaborn for visualizations
- pickle for loading embeddings

## Architecture

### Core Components

1. **Data Loading and Processing**
   - Loads article metadata and pre-computed embeddings
   - Processes click interaction data from multiple CSV files
   - Creates user-article interaction matrices with ~99.8% sparsity

2. **Content-Based Filtering System**
   - **ContentBasedRecommender class**: Main recommendation engine
     - `build_user_profile()`: Creates user profiles from interaction history using weighted averaging of article embeddings
     - `get_recommendations()`: Generates top-N recommendations using cosine similarity
     - `explain_recommendation()`: Provides interpretable explanations for recommendations
   
   - **Article Profiles**: Uses 250-dimensional pre-computed embeddings or category-based features
   - **User Profiles**: Weighted aggregation of interacted article profiles
   - **Similarity Computation**: Cosine similarity between user and article profiles

3. **Evaluation Framework**
   - **RecommenderEvaluator class**: Comprehensive evaluation system
     - `split_data()`: Train/test split preserving user interactions
     - `precision_at_k()`: Measures recommendation accuracy
     - `recall_at_k()`: Measures recommendation coverage
     - `coverage()`: Catalog coverage metric
     - `diversity()`: Category-based diversity metric

### Key Algorithms

- **Profile Building Methods**:
  - `weighted_avg`: Weights articles by interaction count
  - `mean`: Simple average of article profiles
  - `recent`: Time-weighted profiles (placeholder for future implementation)

- **Similarity Metrics Implemented**:
  - Cosine similarity (primary)
  - Euclidean distance
  - Pearson correlation

### Performance Characteristics

- Handles 364,047 articles with 250-dimensional embeddings
- Processes user interactions from 7,982+ users
- Matrix sparsity: ~99.8%
- Current evaluation metrics (on sample data):
  - Precision@5: Low due to sparse test data
  - Diversity: ~0.41 (good category variety)
  - Catalog coverage: 0.06% (231 unique articles recommended)

## Important Implementation Details

- The system loads only first 10 click files by default for performance (lines 15-16 in cell 15)
- User profiles are created for first 100 users as demonstration (line 59 in cell 23)
- Evaluation uses first 50 users to speed up metrics calculation (line 154 in cell 29)
- Embeddings are pre-computed and stored as numpy arrays in pickle format
- The notebook implements visualization functions for analyzing recommendation quality and user behavior patterns