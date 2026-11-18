// CSC418 Lab Midterm - automated ML retraining pipeline
// Job name: MIDTERM-FA23-BCT-059
// Trigger : GitHub push webhook -> http://<EC2-IP>:8080/github-webhook/
pipeline {
    agent any

    triggers {
        githubPush()
    }

    options {
        skipDefaultCheckout()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
        timeout(time: 15, unit: 'MINUTES')
    }

    environment {
        STUDENT_ID = 'FA23-BCT-059'
        NOTIFY_TO  = 'qasimalik@gmail.com'
        IMAGE      = 'midterm-fa23-bct-059'
        DOCKERHUB_REPO = 'zaynisop/midterm-fa23-bct-059'
        CONTAINER  = 'midterm-app'
        APP_PORT   = '8000'
        VENV       = "${env.JENKINS_HOME}/venvs/midterm-fa23-bct-059"
    }

    stages {
        stage('Fetch latest data') {
            steps {
                script {
                    def scmVars = checkout scm
                    env.GIT_COMMIT = scmVars.GIT_COMMIT
                }
                sh '''
                    echo "Commit: $GIT_COMMIT"
                    git log -1 --pretty='%h %an: %s'
                    echo "Dataset rows (incl. header): $(wc -l < dataset/train.csv)"
                '''
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    [ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
                    REQ_HASH=$(cat requirements.txt requirements-dev.txt | sha256sum | cut -c1-16)
                    if [ ! -f "$VENV/.installed-$REQ_HASH" ]; then
                        "$VENV/bin/pip" install -q --upgrade pip
                        "$VENV/bin/pip" install -q -r requirements-dev.txt
                        rm -f "$VENV"/.installed-* && touch "$VENV/.installed-$REQ_HASH"
                    fi
                '''
            }
        }

        stage('Retrain model') {
            steps {
                sh '''
                    rm -rf artifacts
                    "$VENV/bin/python" train.py
                '''
            }
        }

        stage('Test') {
            steps {
                sh '"$VENV/bin/python" -m pytest -q tests --junitxml=reports/junit.xml'
            }
            post {
                always { junit allowEmptyResults: true, testResults: 'reports/junit.xml' }
            }
        }

        stage('Build Docker image') {
            steps {
                sh 'docker build -t "$IMAGE:$BUILD_NUMBER" -t "$IMAGE:latest" .'
            }
        }

        stage('Deploy on EC2') {
            steps {
                sh '''
                    docker rm -f "$CONTAINER" 2>/dev/null || true
                    docker run -d --name "$CONTAINER" --restart unless-stopped \
                        -p "$APP_PORT:8000" "$IMAGE:$BUILD_NUMBER"
                '''
            }
        }

        stage('Verify deployment') {
            steps {
                sh '''
                    for i in $(seq 1 30); do
                        if curl -fsS "http://localhost:$APP_PORT/metrics" -o live-metrics.json \
                           && grep -q "$GIT_COMMIT" live-metrics.json; then
                            echo "Live /metrics:"; cat live-metrics.json; echo
                            exit 0
                        fi
                        sleep 2
                    done
                    echo "Deployed service did not report commit $GIT_COMMIT"; exit 1
                '''
                archiveArtifacts artifacts: 'artifacts/metrics.json', allowEmptyArchive: true
            }
        }

        stage('Push to DockerHub') {
            // Uses the jenkins user's `docker login` (access token stored once on the EC2 host)
            steps {
                sh '''
                    docker tag "$IMAGE:$BUILD_NUMBER" "$DOCKERHUB_REPO:$BUILD_NUMBER"
                    docker tag "$IMAGE:$BUILD_NUMBER" "$DOCKERHUB_REPO:latest"
                    docker push "$DOCKERHUB_REPO:$BUILD_NUMBER"
                    docker push "$DOCKERHUB_REPO:latest"
                '''
            }
        }
    }

    post {
        always {
            script {
                def metrics = fileExists('artifacts/metrics.json') ? readFile('artifacts/metrics.json') : 'metrics not available'
                mail to: env.NOTIFY_TO,
                     subject: "${env.STUDENT_ID} | MIDTERM-${env.STUDENT_ID} build #${env.BUILD_NUMBER}: ${currentBuild.currentResult}",
                     body: """Student Reg No: ${env.STUDENT_ID}
Job: ${env.JOB_NAME}  Build: #${env.BUILD_NUMBER}
Result: ${currentBuild.currentResult}
Commit: ${env.GIT_COMMIT}
Build URL: ${env.BUILD_URL}

Model metrics:
${metrics}
"""
            }
            sh 'docker image prune -f >/dev/null 2>&1 || true'
        }
    }
}
