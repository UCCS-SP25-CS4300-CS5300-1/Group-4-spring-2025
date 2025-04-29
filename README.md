# ApplierPilotAI - Group-4-spring-2025

## Live Site

live site (prod): [https://applierpilot.com/](https://applierpilot.com/)

live site (dev): [https://group-4-spring-2025.fly.dev/](https://group-4-spring-2025.fly.dev/)

## Getting the code

1. Clone the repository:

```bash
git clone https://github.com/UCCS-SP25-CS4300-CS5300-1/Group-4-spring-2025
cd Group-4-spring-2025
```

### Local Development Setup (For just testing stuff locally without worrying about prod or pushing yet)

```bash
## sets up database, runs migrations, admin team, and starts the server
./python-local-test.sh
```

The site will be available at [http://localhost:8000/](http://localhost:8000/)

### Docker Local Testing (do this when you're ready to push to prod)

#### If your code doesn't work in this docker file, it will not work in prod either. GET IT TO WORK HERE FIRST.

```bash
## sets up ssl, builds docker image, and runs the container (plus all the stuff from python-local-test.sh)
./docker-local-test.sh
```

The site will be available at [https://localhost:8000/](https://localhost:8000/)


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

#### Minimum Requirements

- All tests must pass (your commit will fail on actions if they don't)
- All new features must have tests
- Minimum 85% test coverage

### CI Pipeline

The project uses GitHub Actions for CI with the following features:

1. **Automated Testing**: Tests run on every commit and pull request
2. **Coverage Reporting**: Test coverage metrics are reported in the console
3. **AI Code Review**: Pull requests are automatically reviewed using OpenAI's GPT-o3-mini for code quality and style

### Production Deployment

Assuming all tests pass and coverage is above 85%, the CI pipeline will deploy the changes to Fly.io automatically upon pushing to the main branch. (commits or pull requests).
