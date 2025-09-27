Architecture
============

The application contains three primary layers: web, ETL, and database.

Web Layer
---------

Flask application with two blueprints:

**Portfolio Blueprint** (``src/blueprints/portfolio/routes.py``)
    Static routes for home, contact, and projects pages

**Graduate Data Blueprint** (``src/blueprints/grad_data/routes.py``)
    Analysis dashboard with data refresh functionality

ETL Layer
---------

Data pipeline for extracting, transforming, and loading admissions data.

**Extract** (``src/scrape.py``)
    Web scraping TheGradCafe.com with robots.txt compliance
    
    * ``scrape_data()``: Multi-page scraping orchestration
    * ``scrape_page()``: Single page extraction
    * HTML parsing with BeautifulSoup

**Transform** (``src/clean.py``)
    LLM-based data standardization using TinyLlama model
    
    * ``call_llm()``: Program and university name standardization
    * Fuzzy matching against canonical lists
    * Fallback rule-based parsing

**Load** (``src/load_data.py``)
    Data insertion into PostgreSQL database
    
    * ``load_admissions_results()``: Bulk JSON data loading
    * Transaction management
    * Progress reporting

Database Layer
--------------

PostgreSQL database with admission records storage and querying.

**Schema** (``src/model.py``)
    Single table design with comprehensive admission data
    
    * ``AdmissionResult``: Primary dataclass model
    * ``init_tables()``: Table creation
    * UPSERT operations for duplicate handling

**Predefined Analysis Queries** (``src/query_data.py``)
    Predefined analytical queries with formatted output
    
    * ``answer_questions()``: Statistical analysis execution

**Connection Management** (``src/postgres_manager.py``)
    Database lifecycle and connection handling
    
    * ``start_postgres()``: Server initialization
    * ``get_connection()``: Connection pooling
    * Automatic database creation

Data Flow
---------

1. User triggers data refresh via web interface
2. Background thread initiates scraping process
3. Raw HTML data extracted from TheGradCafe.com
4. LLM processes and standardizes university/program names
5. Cleaned data inserted into PostgreSQL with UPSERT
6. Analysis queries executed against stored data
7. Formatted results displayed in web dashboard
