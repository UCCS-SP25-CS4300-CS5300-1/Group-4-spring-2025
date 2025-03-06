# ApplierPilotAI - Group-4-spring-2025


## Live Site

live site: [https://group-4-spring-2025.fly.dev/](https://group-4-spring-2025.fly.dev/)

### Local Development Setup

1. Clone the repository:

```bash
git clone https://github.com/UCCS-SP25-CS4300-CS5300-1/Group-4-spring-2025
cd Group-4-spring-2025
```

2. Set up the database:

```bash
cd myproject
python3 init_db.py
python3 manage.py migrate
```

4. Run the development server:

```bash
python3 manage.py runserver
```

The site will be available at [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### Running Tests

The project (tries to) has comprehensive test coverage. You can run the tests with the following command:

```bash
cd myproject
python3 manage.py test
```

### Test Coverage

To run tests with coverage reporting:

```bash
## From the project root
./run_tests_with_coverage.sh
```

This will generate a coverage report showing what percentage of the code is covered by tests. 

The report will be available in HTML format at `myproject/htmlcov/index.html`.

### Docker Local Testing

1. Build the Docker image:

```bash
docker build -t applierpilotai .
```

2. Run the container locally:

```bash
docker run -p 8000:8000 applierpilotai
```

The site will be available at [http://localhost:8000/](http://localhost:8000/)

For a simplified Docker test, you can use the provided script:

```bash
./docker-local-test.sh
```

### Production Deployment

Ask Kaden.
