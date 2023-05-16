pipeline {
    agent any
    
    stages{
        stage("verify tooling") {
            steps {
                sh '''
                  pwd
                  git --version
                  docker --version
                  docker-compose --version
                  python3 --version
                '''
            }
        }
        
        stage("deploy") {
            steps {
                sh '''
                    export API_ENV=test
                    [ -d "deploy" ] && rm -rf deploy
                    echo $GITHUB_TOKEN
                    git clone -b ${API_ENV} https://${GITHUB_TOKEN}@github.com/lambdamirror/pht-app-deploy.git deploy
                    cd ./deploy
                    docker-compose down
                    docker-compose --env-file ./config/.env.${API_ENV} up -d --force-recreate --build
                    docker ps
                '''
            }
        }
    }
    
}
