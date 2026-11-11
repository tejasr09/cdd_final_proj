pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timestamps()
    }

    environment {
        UV_PYTHON = '/usr/local/bin/python3.11'
        DATABASE_URL = 'sqlite:///./jenkins-ci.sqlite3'
    }

    stages {
        stage('Frontend quality') {
            steps {
                dir('frontend') {
                    sh 'npm ci'
                    sh 'npm run lint'
                    sh 'npm run format:check'
                    sh 'npm run typecheck'
                    sh 'npm test -- --run --pool=forks --maxWorkers=1'
                    sh 'npm audit'
                    sh 'npm run build'
                }
            }
        }

        stage('Backend quality') {
            steps {
                dir('backend') {
                    sh 'uv sync --locked'
                    sh 'uv run --locked ruff check app tests scripts'
                    sh 'uv run --locked ruff format --check app tests scripts'
                    sh 'uv run --locked pytest'
                    sh 'uv run --locked alembic upgrade head'
                    sh 'uv run --locked alembic check'
                    sh 'uv audit --locked'
                }
            }
        }
    }

    post {
        always {
            deleteDir()
        }
    }
}
