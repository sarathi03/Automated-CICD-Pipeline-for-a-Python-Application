# Ultimate DevOps CI/CD Demo --- Detailed Personal Study Guide

**Repository:** https://github.com/sarathi03/devops-cicd-demo\
**Purpose:** Personal revision notes, troubleshooting history,
architecture explanation, and interview preparation.

> Accuracy note: This guide records the implementation and
> troubleshooting supported by our conversation. Where the exact final
> file contents or exact original console output were not preserved, the
> guide labels the example as a reconstructed/reference version. Always
> compare it with the live GitHub repository before copying code into
> production.

------------------------------------------------------------------------

# 1. Executive summary

We built a learning-oriented CI/CD pipeline for a small Python HTTP
application. A developer updates source code locally and pushes it to
the `main` branch on GitHub. A GitHub push webhook reaches Jenkins
running on an Ubuntu EC2 instance. Jenkins checks out the repository,
builds and inspects a Docker image, authenticates to Amazon ECR using
AWS CLI credentials supplied by an EC2 IAM role, tags and pushes the
image, then deploys the image on the same EC2 host as a Docker
container. The deployment stage waits for the app's `/health` endpoint
to return successfully.

The end-to-end update test was completed: after the application response
was changed and pushed, the webhook triggered a Jenkins build and the
running app returned the updated greeting. The `/health` endpoint
returned `OK`.

This is a demonstration project, not a high-availability or
production-hardened platform. Jenkins and the application share one EC2
host; replacing the app container can cause downtime.

# 2. What problem are we solving?

Without CI/CD, every application change could require a person to log
into a server, build a Docker image manually, push it to a registry,
stop the old container, start a new one, and test it. Manual steps are
repetitive and easy to forget.

Our pipeline automates those repeatable steps: - Source changes are
version-controlled in Git. - GitHub notifies Jenkins about a push. -
Jenkins runs the same ordered steps every time. - Docker packages the
app consistently. - ECR stores the image. - The deployment stage
replaces the running container and checks health.

## Outcomes

-   Reduced manual deployment steps.
-   Repeatable image build and publication.
-   A build-number image tag in addition to `latest`.
-   An automatic webhook-triggered build.
-   A basic post-deployment health check.
-   A useful foundation for learning DevOps concepts and explaining them
    in interviews.

It does **not** yet prove zero-downtime deployment, comprehensive test
coverage, automatic monitoring/alerting, or production-grade security.

# 3. Architecture and request flow

``` text
Developer PC (Windows)
  |
  | edit app.py / Dockerfile / Jenkinsfile
  | git diff -> git add -> git commit -> git push origin main
  v
GitHub: sarathi03/devops-cicd-demo (main)
  |
  | Push event -> HTTP POST webhook
  v
AWS EC2: Ubuntu 24.04
  |
  +-- Jenkins on TCP 8080
  |     |
  |     +-- checkout repository
  |     +-- inspect application
  |     +-- docker build
  |     +-- docker image inspect
  |     +-- AWS CLI gets ECR login token via EC2 IAM role
  |     +-- docker push :latest and :BUILD_NUMBER
  |     +-- docker pull :latest
  |     +-- replace devops-cicd-app container
  |     +-- curl localhost:5000/health
  |
  +-- Docker daemon
  |     |
  |     +-- application container: devops-cicd-app
  |           host TCP 5000 -> container TCP 5000
  v
Amazon ECR repository: devops-cicd-demo
```

## Component responsibilities

  -----------------------------------------------------------------------
  Component               Responsibility          Why it is used
  ----------------------- ----------------------- -----------------------
  Git                     Tracks file history and Review/revert code
                          commits                 changes

  GitHub                  Hosts source repository Collaboration and
                                                  webhook events

  GitHub webhook          Sends push notification Avoid manual Build Now
                          to Jenkins              for every push

  Jenkins                 Orchestrates pipeline   Repeatable CI/CD
                          stages                  execution

  Jenkinsfile             Pipeline-as-code        Version the
                          definition              build/deploy process
                                                  with app code

  Dockerfile              Defines image build     Consistent application
                          instructions            packaging

  Docker image            Immutable-ish package   Distribute a particular
                          of app and runtime      app version

  Docker container        Running instance of     Execute the application
                          image                   

  ECR                     Private container       Store and version built
                          registry                images

  EC2                     VM hosting Jenkins and  Compute for the demo
                          app                     

  IAM instance role       Grants temporary AWS    Avoid static access
                          permissions             keys in source code

  `curl` health check     Calls `/health` after   Detect basic startup
                          deployment              failure
  -----------------------------------------------------------------------

# 4. Environment and resource inventory

  ------------------------------------------------------------------------------------------------------
  Item                                Value from the project
  ----------------------------------- ------------------------------------------------------------------
  Repository                          `https://github.com/sarathi03/devops-cicd-demo`

  Branch                              `main`

  Local Windows folder                `C:\Users\Sarathi\devops-cicd-demo`

  AWS region                          `ap-south-1` (Mumbai)

  AWS account ID used                 `141553305146`

  EC2 OS                              Ubuntu 24.04

  EC2 host shown in shell             `ip-172-31-7-168`

  Jenkins URL used after IP           `http://3.109.206.16:8080` at that time
  correction                          

  Jenkins job                         `devops-cicd-pipeline`

  Jenkins port                        `8080`

  ECR repository                      `devops-cicd-demo`

  ECR image URI                       `141553305146.dkr.ecr.ap-south-1.amazonaws.com/devops-cicd-demo`

  Container name                      `devops-cicd-app`

  App port                            `5000`

  ECR IAM role                        `EC2-ECR-Access-Role`
  ------------------------------------------------------------------------------------------------------

**Do not assume the public IPv4 address remains the same.** An earlier
webhook used `3.110.194.58` and GitHub reported
`failed to connect to host`. The current address at the time of fixing
was `3.109.206.16`; changing the webhook to the current address made
delivery succeed. Check the EC2 console before using any address.

# 5. Application source: `app.py`

The application uses Python's built-in `http.server`; it does not use
Flask/FastAPI. It listens on all container interfaces at port `5000`.

Reference version used for the end-to-end update test:

``` python
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        print(f"Received request: {self.path}", flush=True)

        if self.path == "/health":
            body = b"OK"
        else:
            body = b"Version 2 - Automated CI/CD Deployment Successful!"

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
        self.wfile.flush()

    def log_message(self, format, *args):
        print(f"HTTP: {format % args}", flush=True)

server = ThreadingHTTPServer(("0.0.0.0", 5000), AppHandler)
print("Application running on http://127.0.0.1:5000", flush=True)
server.serve_forever()
```

**Important:** This is the functional code recorded in the project
discussion with the updated greeting. The earlier greeting was
`Hello from my DevOps CI/CD application!`. Check the current
repository's `app.py` for the exact final committed content.

## How it works

-   `BaseHTTPRequestHandler` provides request handling.
-   `do_GET()` runs for incoming HTTP GET requests.
-   `self.path == "/health"` returns `OK`.
-   Other GET paths return the greeting.
-   `send_response(200)` sends HTTP status 200.
-   `Content-Type` says the response is plain text and UTF-8.
-   `Content-Length` tells the client the number of bytes.
-   `end_headers()` completes response headers.
-   `wfile.write(body)` writes the response body.
-   `flush=True` makes printed logs appear without waiting for
    buffering.
-   `ThreadingHTTPServer` can serve concurrent requests using separate
    threads.
-   `0.0.0.0` lets the server listen on all container network
    interfaces; Docker port mapping controls host access.

## Test it

``` bash
curl -i http://localhost:5000/health
curl http://localhost:5000/
```

Expected health body: `OK`. Expected root body: the currently committed
greeting.

# 6. Dockerfile --- full code and explanation

``` dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY app.py .
EXPOSE 5000
CMD ["python", "-u", "app.py"]
```

Line by line: - `FROM python:3.12-slim`: uses the Python 3.12 slim base
image. - `WORKDIR /app`: sets the working directory inside the image. -
`COPY app.py .`: copies the application file into `/app`. -
`EXPOSE 5000`: documents the app's container port; it does **not** open
the EC2 security group. - `CMD ["python", "-u", "app.py"]`: starts the
app with unbuffered Python output.

Build and inspect locally/on the EC2 Jenkins host:

``` bash
docker build -t devops-cicd-demo:latest .
docker image inspect devops-cicd-demo:latest
docker image ls devops-cicd-demo:latest
```

# 7. Jenkinsfile --- pipeline structure and reference implementation

The repository's `Jenkinsfile` is the source of truth. The following is
a consolidated reference based on the stages and commands discussed.
Compare it with the current committed Jenkinsfile before replacing
anything. It includes a rollback attempt, but that rollback is not a
guarantee of zero downtime and should be tested carefully.

``` groovy
pipeline {
    agent any

    options {
        timestamps()
    }

    stages {
        stage('Checkout Verification') {
            steps {
                echo 'Jenkins has loaded the pipeline.'
                sh 'whoami'
                sh 'pwd'
                sh 'ls -la'
            }
        }

        stage('Application Check') {
            steps {
                sh 'python3 --version || true'
                sh 'cat app.py'
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker build -t devops-cicd-demo:latest .'
            }
        }

        stage('Docker Image Verification') {
            steps {
                sh 'docker image inspect devops-cicd-demo:latest'
                sh 'docker image ls devops-cicd-demo:latest'
            }
        }

        stage('Push Image to Amazon ECR') {
            steps {
                sh '''
                    set -eu

                    AWS_REGION="ap-south-1"
                    AWS_ACCOUNT_ID="141553305146"
                    ECR_REPOSITORY="devops-cicd-demo"
                    ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
                    ECR_IMAGE="${ECR_REGISTRY}/${ECR_REPOSITORY}"

                    /usr/local/bin/aws ecr get-login-password \
                        --region "$AWS_REGION" \
                    | docker login \
                        --username AWS \
                        --password-stdin "$ECR_REGISTRY"

                    docker tag devops-cicd-demo:latest "${ECR_IMAGE}:latest"
                    docker tag devops-cicd-demo:latest "${ECR_IMAGE}:${BUILD_NUMBER}"

                    docker push "${ECR_IMAGE}:latest"
                    docker push "${ECR_IMAGE}:${BUILD_NUMBER}"
                '''
            }
        }

        stage('Deploy Application') {
            steps {
                sh '''
                    set -eu

                    APP_NAME="devops-cicd-app"
                    AWS_REGION="ap-south-1"
                    AWS_ACCOUNT_ID="141553305146"
                    ECR_REPOSITORY="devops-cicd-demo"
                    ECR_IMAGE="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPOSITORY}"

                    echo "Pulling the latest image from ECR..."
                    docker pull "${ECR_IMAGE}:latest"

                    echo "Saving the current image for rollback..."
                    OLD_IMAGE_ID=$(docker inspect --format='{{.Image}}' "$APP_NAME" 2>/dev/null || true)

                    echo "Removing the old container..."
                    docker rm -f "$APP_NAME" || true

                    echo "Starting the new application container..."
                    if ! docker run -d \
                        --name "$APP_NAME" \
                        --restart unless-stopped \
                        -p 5000:5000 \
                        "${ECR_IMAGE}:latest"; then

                        echo "New container failed to start. Rolling back..."
                        if [ -n "$OLD_IMAGE_ID" ]; then
                            docker run -d \
                                --name "$APP_NAME" \
                                --restart unless-stopped \
                                -p 5000:5000 \
                                "$OLD_IMAGE_ID"
                        fi
                        exit 1
                    fi

                    echo "Waiting for the application health check..."
                    HEALTHY=false

                    for attempt in 1 2 3 4 5 6 7 8 9 10; do
                        if curl -fsS http://localhost:5000/health; then
                            HEALTHY=true
                            break
                        fi
                        echo "Health check attempt $attempt failed; retrying..."
                        sleep 3
                    done

                    if [ "$HEALTHY" != "true" ]; then
                        echo "Health check failed. Rolling back..."
                        docker logs "$APP_NAME" || true
                        docker rm -f "$APP_NAME" || true

                        if [ -n "$OLD_IMAGE_ID" ]; then
                            docker run -d \
                                --name "$APP_NAME" \
                                --restart unless-stopped \
                                -p 5000:5000 \
                                "$OLD_IMAGE_ID"
                        fi

                        exit 1
                    fi

                    echo "Deployment successful!"
                '''
            }
        }

        stage('Pipeline Success') {
            steps {
                echo 'Checkout, build, image verification, ECR push, and deployment completed!'
            }
        }
    }

    post {
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed. Check the console output.'
        }
    }
}
```

## Jenkinsfile concepts

-   `pipeline {}`: declarative pipeline definition.
-   `agent any`: execute on any available Jenkins agent; this setup uses
    the built-in/controller environment.
-   `options { timestamps() }`: add timestamps to console log lines.
-   `stages`: ordered workflow stages.
-   `steps`: commands/actions in a stage.
-   `sh`: runs shell commands on the Linux Jenkins node.
-   `BUILD_NUMBER`: Jenkins-provided environment variable for the build
    number.
-   `post { success / failure }`: print a final message based on
    pipeline outcome.

## Important caveats in this deployment script

1.  The app container is removed before the new one is proven healthy.
    That creates downtime during replacement.
2.  Rollback uses the prior container's immutable image ID, which is
    more robust than relying on the mutable `latest` tag, but the
    rollback path still needs a deliberate failure test.
3.  `docker run -d` can succeed even if the process exits immediately
    afterward; the health check is therefore important.
4.  The script assumes `curl` exists on the EC2 host and the Jenkins
    user can use Docker.
5.  It uses the `latest` tag for deployment. Build-number tags are more
    traceable for future releases.
6.  The health check confirms the HTTP endpoint responds; it does not
    validate every application behavior.
7.  This is a learning deployment, not a zero-downtime release system.

# 8. Git workflow --- exact commands and purpose

From Windows PowerShell/Git Bash in the project folder:

``` bash
cd C:\Users\Sarathi\devops-cicd-demo
git status
git diff app.py
git diff Jenkinsfile
git add app.py
git commit -m "Test automated application deployment"
git push origin main
```

Typical workflow: 1. Edit a file. 2. `git diff` to review changes. 3.
`git add` to stage the intended file. 4. `git commit` to save a local
snapshot. 5. `git push origin main` to publish it.

A webhook test commit had the message `Test GitHub webhook automation`.
It changed `README.md`. That webhook initially could not connect because
the configured endpoint used an outdated public IP.

# 9. GitHub webhook --- configuration and troubleshooting

Configured in repository **Settings → Webhooks**: - Payload URL pattern:
`http://CURRENT_EC2_PUBLIC_IP:8080/github-webhook/` - Content type:
`application/json` - Event: `Just the push event` - Jenkins job trigger:
`GitHub hook trigger for GITScm polling`

## What happened

GitHub delivery returned `failed to connect to host`. On EC2, these
checks showed Jenkins was running locally:

``` bash
sudo systemctl status jenkins --no-pager
sudo ss -lntp | grep ':8080'
curl -I --max-time 5 http://localhost:8080/login
```

The Jenkins service was active, port `8080` was listening, and localhost
returned `HTTP/1.1 200 OK`. The public IP had changed. Updating the
webhook payload URL to the current IP allowed delivery to succeed; a
Jenkins build was then triggered automatically.

## What this taught us

-   `systemctl status` verifies service state.
-   `ss -lntp` checks whether a process is listening on a TCP port.
-   `curl localhost` tests the local service only.
-   GitHub webhook delivery tests whether GitHub can reach the
    configured endpoint.
-   A successful delivery is not enough by itself; Jenkins Build History
    and Console Output must also be checked.

## Future improvement

A changing EC2 public IP can break the webhook again. Use a stable DNS
name and secure HTTPS endpoint when hardening the project. Do not expose
Jenkins broadly without access controls.

# 10. Jenkins configuration

Job: `devops-cicd-pipeline`

Expected configuration: - **Pipeline definition:** Pipeline script from
SCM - **SCM:** Git - **Repository:**
`https://github.com/sarathi03/devops-cicd-demo` - **Branch:** `*/main` -
**Script Path:** `Jenkinsfile` - Public repository, so checkout used no
Git credentials. - Build trigger includes GitHub webhook trigger for
GITScm polling.

The Jenkins UI reads the `Jenkinsfile` from GitHub. This is called
**Pipeline as Code**.

## Useful diagnostics

``` bash
sudo systemctl status jenkins --no-pager
sudo ss -lntp | grep ':8080'
curl -I --max-time 5 http://localhost:8080/login
```

A Git installation warning appeared
(`Selected Git installation does not exist. Using Default...`). Checkout
still worked. It was non-blocking, but Jenkins Global Tool Configuration
can be cleaned up later.

# 11. Docker operations and issues

Useful commands:

``` bash
sudo docker ps
sudo docker ps -a
sudo docker images
sudo docker logs devops-cicd-app
sudo docker inspect devops-cicd-app --format '{{json .HostConfig.PortBindings}}'
sudo docker inspect devops-cicd-app --format '{{.State.OOMKilled}}'
```

Manual deployment used for the first app test:

``` bash
sudo docker run -d \
  --name devops-cicd-app \
  --restart unless-stopped \
  -p 5000:5000 \
  141553305146.dkr.ecr.ap-south-1.amazonaws.com/devops-cicd-demo:latest
```

The old container name was already present in stopped state. We
inspected it, removed it, and started a replacement. The running
container showed `0.0.0.0:5000->5000/tcp`.

Tests:

``` bash
curl -i http://localhost:5000/health
curl http://localhost:5000/
```

## Exit code 137

A previous container showed `Exited (137)`, but `.State.OOMKilled` was
`false`. Code 137 typically means the process received SIGKILL, but the
exact cause was not established in this exercise. Do not record it as
definitely an OOM issue.

If it occurs again:

``` bash
sudo docker logs devops-cicd-app
sudo docker inspect devops-cicd-app
sudo journalctl -u docker --since "1 hour ago" --no-pager
```

## Why a container name conflict happens

Docker container names must be unique, including names used by stopped
containers. `docker ps` only lists running containers; `docker ps -a`
also lists stopped containers. Inspect before removing anything.

# 12. Amazon ECR --- image storage and push

ECR repository: - Name: `devops-cicd-demo` - Region: `ap-south-1` - URI:
`141553305146.dkr.ecr.ap-south-1.amazonaws.com/devops-cicd-demo`

Pipeline actions: 1. Get an ECR authentication password using AWS CLI.
2. Pass the password to `docker login` over standard input. 3. Tag the
local image with ECR URI and `latest`. 4. Tag it again with Jenkins
`BUILD_NUMBER`. 5. Push both tags.

Core commands from the pipeline:

``` bash
AWS_REGION="ap-south-1"
AWS_ACCOUNT_ID="141553305146"
ECR_REPOSITORY="devops-cicd-demo"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
ECR_IMAGE="${ECR_REGISTRY}/${ECR_REPOSITORY}"

/usr/local/bin/aws ecr get-login-password --region "$AWS_REGION" \
  | docker login --username AWS --password-stdin "$ECR_REGISTRY"

docker tag devops-cicd-demo:latest "${ECR_IMAGE}:latest"
docker tag devops-cicd-demo:latest "${ECR_IMAGE}:${BUILD_NUMBER}"
docker push "${ECR_IMAGE}:latest"
docker push "${ECR_IMAGE}:${BUILD_NUMBER}"
```

The ECR push stage succeeded in Jenkins and both `latest` and a
build-number tag were pushed. The digest seen for one successful image
was
`sha256:c3dffa53d47cd199e9a6bd6d7158830dc753dc7e93889a49a1ed39e4ca61bfb3`.

## Why two tags?

-   `latest` is a convenient pointer to the most recently pushed image
    with that tag.
-   A build-number tag identifies a particular Jenkins build's image and
    helps compare releases.
-   `latest` alone is less traceable because it changes when pushed
    again.

# 13. IAM and credentials

The EC2 instance had an IAM role named `EC2-ECR-Access-Role` attached.
AWS CLI was installed at `/usr/local/bin/aws`.

Identity check:

``` bash
sudo -u jenkins /usr/local/bin/aws sts get-caller-identity
```

This returned account ID `141553305146` and an assumed role identity.
Jenkins could log in to ECR and push the image, demonstrating that the
instance role provided sufficient permissions for the pipeline actions
performed.

## Why an IAM role instead of access keys?

The role lets the EC2 workload obtain temporary credentials. It avoids
putting long-lived AWS secret keys in a Jenkinsfile, shell script, or
GitHub repository.

## IAM follow-up

The exact policy JSON attached to the role was not retained in the
notes, so this guide does not claim the policy is least-privilege.
Review it in IAM and restrict it to the ECR operations and repository
resources required by this pipeline.

# 14. EC2 and networking

The Jenkins server was Ubuntu 24.04 on EC2. Jenkins listened on port
`8080`; the application used host port `5000`. Docker port mapping was
`-p 5000:5000`.

Security Groups are cloud firewalls. A port mapping in Docker does not
override the EC2 Security Group. A process listening on `0.0.0.0` does
not automatically mean the internet can reach it; routing and firewall
rules also matter.

## Critical security action

An earlier Security Group screenshot showed a broad inbound rule for all
TCP ports `0–65535` from `0.0.0.0/0`. The notes do not establish whether
it remains in the current configuration. Check it and remove it if
present.

Suggested direction: - SSH TCP `22`: only your trusted public IP. -
Jenkins TCP `8080`: restrict to your own IP while testing, or put it
behind a secured HTTPS access path. - App TCP `5000`: do not expose
publicly unless required; if needed, restrict source access. - Never
leave all TCP ports open to the world.

Because the webhook must reach Jenkins, do not blindly restrict port
`8080` to your own IP and expect GitHub webhooks to continue working.
Plan a secure webhook ingress path (for example HTTPS via a reverse
proxy) before changing network rules that the webhook relies on.

# 15. Errors, root causes, and fixes

  --------------------------------------------------------------------------------------------------
  Symptom                       What we checked                  Root cause /      Fix or lesson
                                                                 status            
  ----------------------------- -------------------------------- ----------------- -----------------
  GitHub:                       Jenkins service, port listener,  Jenkins worked    Update payload
  `failed to connect to host`   localhost curl                   locally; webhook  URL to current
                                                                 URL used old      EC2 public IP
                                                                 public IP         

  Jenkins Git tool warning      Checkout output                  Warning was       Configure correct
                                                                 non-blocking;     Git installation
                                                                 checkout worked   later

  Docker name conflict          `docker ps -a`                   Stopped container Inspect and
                                                                 retained the name remove old
                                                                                   container only if
                                                                                   safe

  Container exited `137`        `docker inspect ... OOMKilled`   Exact cause not   Inspect logs and
                                                                 established;      Docker/system
                                                                 OOMKilled false   journal if
                                                                                   repeated

  Need to know if deployment    `docker ps`, `curl /health`,     Container was up  Verify app
  worked                        root URL                         and health        response after
                                                                 returned `OK`     each deployment

  Need to prove webhook         GitHub Recent Deliveries +       Delivery and      Do not rely on
  automation                    Jenkins Build History            automatic build   GitHub green tick
                                                                 were observed     alone
  --------------------------------------------------------------------------------------------------

# 16. End-to-end update test --- runbook

The test proves that the entire chain updates the running application
after a source change.

## A. Make a visible app change

In `app.py`, change the non-health response to a new message. Keep the
`/health` response as `OK`.

Review:

``` bash
git diff app.py
```

## B. Commit and push

``` bash
git add app.py
git commit -m "Test automated application deployment"
git push origin main
```

Do not click **Build Now** while testing webhook automation.

## C. Confirm webhook and build

1.  GitHub repository → Settings → Webhooks → Recent Deliveries.
2.  Confirm the push event delivery is successful.
3.  Jenkins → `devops-cicd-pipeline` → Build History.
4.  Open the new build → Console Output.
5.  Check the Docker build, ECR push, Deploy Application and
    health-check output.

## D. Confirm live app

On EC2:

``` bash
sudo docker ps
curl http://localhost:5000/
curl http://localhost:5000/health
```

Expected: the new greeting and `OK`. During the test, this succeeded and
the container was running with host port `5000` mapped to container port
`5000`.

# 17. What use cases can this pattern serve?

This basic pattern is useful for learning or small internal services
such as: - A demo REST/HTTP service. - A small Python API or internal
tool. - A proof-of-concept application. - A test/staging environment. -
A personal project where a code push should publish and deploy a
container.

The pattern can be adapted to a .NET API, Node.js service, or another
containerized workload by changing application checks, Dockerfile,
tests, and runtime configuration.

For larger production systems, consider: - Unit/integration tests before
building or deploying. - Separate dev/staging/prod environments. -
Immutable image tags and deployment by exact digest. - Blue/green or
rolling deployment with load balancing. - Health checks and automatic
rollback tested in a staging environment. - HTTPS, secrets management,
network segmentation, and least-privilege IAM. - Logs, metrics,
alerting, backups, and deployment approvals. - A dedicated Jenkins agent
or build service rather than building/deploying everything on one
controller host.

# 18. STAR-format interview story

## Situation

I wanted to understand and demonstrate an end-to-end CI/CD workflow for
a containerized application, including source control, automated build,
image storage, and deployment on AWS.

## Task

My goal was to configure GitHub to notify Jenkins automatically on a
push, build and verify the Docker image, publish it to Amazon ECR,
deploy it to an EC2-hosted container, and verify the service health.

## Action

I created a small Python HTTP service with a `/health` endpoint and
wrote a Dockerfile to package it. I stored the project and Jenkinsfile
in a GitHub repository and configured a Jenkins Pipeline job using
Pipeline script from SCM. I attached an EC2 IAM role for AWS access,
used AWS CLI to authenticate Docker to ECR, and configured the pipeline
to push both `latest` and Jenkins build-number tags. I added a
deployment stage to pull the ECR image, replace the running container,
and poll the health endpoint. When GitHub webhook delivery failed, I
checked the Jenkins service, listener port, and local HTTP response; I
then identified that the webhook URL used an outdated EC2 public IP and
updated it. I also investigated a stopped container/name conflict and
verified the app using Docker and curl.

## Result

The GitHub push webhook successfully triggered Jenkins, the pipeline
completed successfully, ECR image pushes were confirmed, the application
container ran on port `5000`, and the health endpoint returned `OK`.
After changing the application greeting and pushing the update, the
deployed app returned the new message, demonstrating the end-to-end
update flow.

## Interview-ready concise version

"I built a learning CI/CD pipeline using GitHub, Jenkins, Docker, Amazon
ECR, IAM, and EC2. A GitHub push webhook triggers Jenkins, which checks
out the code, builds and verifies the Docker image, pushes both `latest`
and build-number tags to ECR using the EC2 instance role, and deploys
the image as a container on EC2. I added a `/health` endpoint check to
validate deployment. I troubleshot webhook delivery by checking Jenkins
service status, its listening port, and local HTTP response, then
corrected the outdated EC2 public IP in the webhook URL. I verified the
final flow by pushing an application change and confirming the new
response from the running container."

**Interview honesty note:** Describe it as a working learning/demo
pipeline. Do not claim zero-downtime deployment, production readiness,
comprehensive automated tests, or least-privilege IAM unless those have
been implemented and verified.

# 19. Common interview questions and answers

### Why use Jenkins?

Jenkins automates the sequence of checkout, build, image publication,
deployment, and validation so each code push follows a repeatable
workflow.

### Why a Jenkinsfile?

It keeps pipeline logic as code in version control, so changes to the
pipeline can be reviewed and versioned along with the application.

### Why Docker?

Docker packages the application and its runtime into an image, reducing
differences between environments.

### Why ECR?

ECR is a private AWS registry that stores container images so deployment
hosts can pull them.

### Why IAM role?

An EC2 instance role supplies temporary AWS credentials, avoiding
hard-coded long-lived credentials in source code.

### What does the webhook do?

GitHub sends an HTTP request when a configured event, such as a push,
occurs. Jenkins uses the event to start the job's SCM polling/trigger
workflow.

### Why tag images with a build number?

The tag helps identify which Jenkins build produced an image. It is more
traceable than using only the mutable `latest` tag.

### What does `/health` verify?

It checks that the app responds to an HTTP request. It is a basic
availability check, not a full functional test.

### What was the main issue?

GitHub could not connect to Jenkins because the webhook payload URL used
an outdated EC2 public IP. Jenkins was healthy locally; correcting the
endpoint fixed webhook delivery.

### What would you improve next?

Secure Jenkins with HTTPS and restricted access, remove broad Security
Group rules, review IAM least privilege, add automated tests, use
immutable image references, and design a deployment strategy that
reduces downtime.

# 20. Pause and stop the project

If you want to pause the whole environment, stop the EC2 instance from
the AWS console. Jenkins and the application will be unavailable until
it starts again. Compute billing generally stops while stopped, but EBS
volumes, snapshots, ECR storage, and other resources may continue to
incur charges.

If only the application needs to stop while Jenkins stays online:

``` bash
sudo docker stop devops-cicd-app
```

Start it again:

``` bash
sudo docker start devops-cicd-app
```

Do not terminate the EC2 instance or delete the ECR repository unless
you intentionally want to remove project resources.

# 21. Final revision checklist

-   [ ] Explain Git add/commit/push.
-   [ ] Explain what the webhook sends and why the URL must point to the
    current endpoint.
-   [ ] Explain Jenkins SCM configuration and the Jenkinsfile stages.
-   [ ] Explain the Dockerfile line by line.
-   [ ] Explain ECR registry URI, authentication, tags, and push.
-   [ ] Explain why EC2 uses an IAM role.
-   [ ] Explain Docker container name, restart policy, and port mapping.
-   [ ] Explain what `curl /health` proves and what it does not prove.
-   [ ] Recall the webhook public-IP issue and how it was diagnosed.
-   [ ] Recall the container name conflict and exit code 137
    investigation.
-   [ ] Explain remaining security risks and proposed improvements.
-   [ ] Practice the STAR story without overstating production
    readiness.

------------------------------------------------------------------------

## One-minute project explanation

"I built an end-to-end CI/CD demo for a Python HTTP application. Source
code and a Jenkinsfile are stored in GitHub. A push webhook triggers
Jenkins on an Ubuntu EC2 instance. Jenkins checks out the code, builds
and verifies a Docker image, authenticates to Amazon ECR using the EC2
IAM role, and pushes `latest` and build-number tags. The deployment
stage pulls the image and runs it as `devops-cicd-app` on port `5000`,
then checks `/health`. I debugged a webhook connectivity issue by
confirming Jenkins was listening and healthy locally, then correcting
the outdated public IP in GitHub. Finally, I pushed an application
change and verified that the new greeting was served by the deployed
container. The next improvements are security hardening, least-privilege
review, stronger tests, and a deployment strategy that minimizes
downtime."
