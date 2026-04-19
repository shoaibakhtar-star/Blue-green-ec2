pipeline {
    agent any

    environment {
        IMAGE_NAME = "app-image"
        BLUE_NAME = "blue-app"
        GREEN_NAME = "green-app"
        NETWORK = "app-network"
        BLUE_PORT = "8001"
        GREEN_PORT = "8002"
        NGINX_CONF = "nginx.conf"
    }

    stages {

        stage('Clone') {
            steps {
                checkout scm
            }
        }

        stage('Build Docker Image') {
            steps {
                sh 'docker build -t $IMAGE_NAME .'
            }
        }

        stage('Ensure Network') {
            steps {
                sh '''
                docker network inspect ${NETWORK} >/dev/null 2>&1 || docker network create ${NETWORK}
                '''
            }
        }

        stage('Detect Active Environment') {
            steps {
                script {
                    def isBlueRunning = sh(
                        script: "docker ps --format '{{.Names}}' | grep ${BLUE_NAME} || true",
                        returnStdout: true
                    ).trim()

                    if (isBlueRunning) {
                        env.ACTIVE = "blue"
                        env.NEW = "green"
                        env.NEW_NAME = GREEN_NAME
                        env.NEW_PORT = GREEN_PORT
                    } else {
                        env.ACTIVE = "green"
                        env.NEW = "blue"
                        env.NEW_NAME = BLUE_NAME
                        env.NEW_PORT = BLUE_PORT
                    }

                    echo "Active: ${env.ACTIVE}, Deploying: ${env.NEW}"
                }
            }
        }

        stage('Deploy New Container') {
            steps {
                sh '''
                docker stop ${NEW_NAME} || true
                docker rm ${NEW_NAME} || true

                docker run -d \
                  --name ${NEW_NAME} \
                  --network ${NETWORK} \
                  --restart unless-stopped \
                  -p ${NEW_PORT}:8000 \
                  ${IMAGE_NAME}
                '''
            }
        }

        stage('Health Check') {
            steps {
                script {
                    sleep 5
                    def retries = 5
                    def success = false

                    for (int i = 0; i < retries; i++) {
                        echo "Health check attempt ${i+1}..."

                        def status = sh(
                            script: """
                            curl -o /dev/null -s -w "%{http_code}" http://localhost:${env.NEW_PORT}/health || true
                            """,
                            returnStdout: true
                        ).trim()

                        if (status == "200") {
                            success = true
                            break
                        }

                        sleep 5
                    }

                    if (!success) {
                        error "Health check failed! Deployment aborted."
                    }
                }
            }
        }

        stage('Switch Traffic (Nginx)') {
            steps {
                script {
                    sh """
                    sed -i 's/server .*;/server ${NEW_NAME}:8000;/' ${NGINX_CONF}
                    docker cp ${NGINX_CONF} nginx:/etc/nginx/nginx.conf
                    docker exec nginx nginx -s reload
                    """
                }
            }
        }

        stage('Stop Old Container') {
            steps {
                script {
                    def oldName = (env.ACTIVE == "blue") ? env.BLUE_NAME : env.GREEN_NAME

                    sh """
                    docker stop ${oldName} || true
                    docker rm ${oldName} || true
                    """
                }
            }
        }

        stage('Cleanup') {
            steps {
                sh 'docker image prune -f'
            }
        }
    }

    post {
        success {
            echo 'Deployment successful with zero downtime'
        }
        failure {
            echo 'Deployment failed. Old version is still serving traffic'
        }
    }
}
