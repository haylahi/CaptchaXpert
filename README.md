# CaptchaXpert
CaptchaXpert is a free and open-source web application available on GitHub. It provides advanced captcha solving services using machine learning and artificial intelligence algorithms. With CaptchaXpert, users can easily integrate captcha solving functionality into their own applications or websites.

To use CaptchaXpert, users will need to set up their environment with the necessary dependencies and libraries. The CaptchaXpert GitHub repository provides detailed instructions on how to install and set up the application on a local machine. Once set up, users can take advantage of CaptchaXpert's advanced features and functionality to solve a wide range of captcha types, including reCaptcha, hCaptcha, antibotlinks captcha, gp captcha.

The CaptchaXpert repository also provides comprehensive documentation on how to use the application's API and how to integrate it into different programming languages and frameworks. This documentation makes it simple for developers and website owners to integrate CaptchaXpert into their projects.

Overall, CaptchaXpert is a reliable and efficient captcha solving service that is essential for any application or website that requires captcha solving functionality. Its free and open-source nature, combined with its advanced algorithms and comprehensive documentation, make it an excellent solution for developers and website owners looking to improve user experience and increase automation capabilities.

# Quick Start
Get started with this project quickly by following these simple steps:

<details open>
<summary>Install</summary>

Run the following command in your terminal to clone the repository: `git clone https://github.com/M-Zubair10/CaptchaXpert.git`

Alternatively, you can download the ZIP file from GitHub.

</details>

<details open>
<summary>Setting up resolver app</summary>

1. Run the following command to navigate to the CaptchaResolver directory: `cd CaptchaResolver`
2. Install the resolver dependencies by running the following command: `pip install -r requirements.txt`
3. Start the app by running the following command: `py -m app` in windows and `python -m app` in linux

</details>

<details open>
<summary>Test Captcha Solver</summary>

1. Navigate to the `api` directory by running the following command: `cd api`
2. Install the api dependencies by running the following command: `pip install -r requirements.txt`
3. Navigate back to the project root directory by running the following command: `cd ..`
4. Run the following command to start the test case: `py -m api.testcase`
5. Copy the `api` directory to your project and use: `from api import CaptchaSolver`
6. See documentation on how to use `CaptchaSolver`

</details>

<details open>
<summary>Setting up Token Solving app</summary>

1. Navigate to the `TokenSolver` directory by running the following command: `cd TokenSolver`
2. Install the token solver dependencies by running the following command: `pip install -r requirements.txt`
3. Start the app by running the following command: `py -m app`
4. Test the app using: `py -m test`

</details>

# <div align="center">Documentation</div>

Full documentation on Captcha Solving, Token Solving, and Captcha Resolver

- [Captcha Resolver](#captcha-resolver)
    - [Endpoints](#endpoints)
    - [Sample request](#sample-request)
      - [Valid types](#valid-types)
      - [Valid data](#valid-data)
    - [Models](#models)
    - [Debugger](#debugger)
- [High Level API](#high-level-api)
  - [Captcha Solver](#captchasolver)
  - [Token Solver](#tokensolver)
  - [Test Cases](#testcases)
- [Token Solver](#token-solver)

# Captcha Resolver

This is the flask app used to solve captcha images, this contains all the required models, and techniques to solve captchas

Anyone can use this app to solve captcha images by sending http request to endpoint

## Endpoints
- `http://127.0.0.1:5000`
- `http://0.0.0.0:5000`

## Sample request

1. Send http request on: `endpoint/resolve`
2. Sample data: `{'type': 'hcaptcha', 'images': list_of_base64_images, 'prompt': 'Please click each image containing a duck.'}`

### Valid types
- hcaptcha
- recaptcha
- antibot

### Payloads
- hCaptcha: `{'type': 'hcaptcha', 'images': list_of_base64_images, 'prompt': 'Please click each image containing a duck.'}`
- reCaptcha: `{'type': 'recaptcha', 'images': list_of_base64_images, 'label': 'bus', grid: '3x3'}`
    - images is divided into 2 parts: `image or images`
         - image: when single image needs to be solved
         - images: when multiple images needs to be solved
    - grid is divided into 3 parts: `1x1 or 3x3 or 4x4`
        - 1x1: used for classifying-task that contains 1 image, appear after clicking any image from 3x3 grid
        - 3x3: used for classifying-task that contains 9 images
        - 4x4: used for detection-task that contains 16 images
- AntibotLinks: `{'type': 'antibot', 'images': list_of_base64_images}`
   
## Models
- hCaptcha:
    - path: `openai/clip-vit-base-patch32`
    - labels-path: `/solutions/hcaptcha/label_map.yaml`
    - description: When new label come, inspect the possible antilabels for that class, and write all label and antilabel in label_map.yaml to update model
- reCaptcha:
    - path: `/solutions/models`
    - labels-path: `/solutions/labels/objects.yaml`
    - updating-models: add model to `$path` and label to `labels-path`
- AntibotLinks:
    - path: `/solutions/antibot/antibot.onnx`
    - updating-models: replace the model with new one, and write corresponding `predict` function in `inference.py`

### Debugger
I currently use `debugger=True` in `intercept.intercept`, which saves the request data if it is failed to resolve

Debugger directory named `debugger` will be generated in `root` directory, which will help us train new models

# High Level API
API to use Captcha Solver with ease

You can import this api in any of your project

It contains the CaptchaSolver, TokenSolver classes and testcases to check your CaptchaSolver accuracy 

## CaptchaSolver

- Import CaptchaSolver class to your project using: `from api import CaptchaSolver`
- Initialize your captcha solver using: `solver = CaptchaSolver()`
  - **parameters**:
     - driver: selenium webdriver, `default=None`, this parameter must be set in order to solve captchas
     - timeout: timeout captcha after given time, `default=60`
     - destroy_storage: destroy temporary storage after solving captcha, `default=True`
     - make_storage: make storage to save captcha content, `default=True`
     - make_storage_at: storage path, `default=/temp_cache`
     - image_getting_method: method to get image either using screenshot or request, `default=screenshot`
     - callback_at: callback to human captcha solving service if retries == callback_at, you can implement you own
                          callbacks in corresponding classes, I used twocaptcha, `default=None`
     - host: endpoint where your captcha-resolver app is hosted, `default=http://127.0.0.1:5000`
     - hook_frame: solve captcha on custom hook frame, see test case2 or case4 for further info, useful if multiple captchas on single page, `default=None`
     - challenge_frame: solve captcha on custom challenge frame, `default=None`
     - response_locator: locator from where response of captcha is checked, useful if multiple captchas on single page, `default=None`
- Set captcha type using: `solver.setCaptchaTypeAsHcaptcha()` or `solver.setCaptchaTypeAsAntiBotLinks()` or `solver.setCaptchaTypeAsRecaptchaV2()` or `solver.setCaptchaTypeAsGpCaptcha()`
- Finally, solve captcha using: `solver.solve(), optional: next_locator=<next-possible-locator> useful in invisible captcha solving`
- Code snippet: 
```
from api import CaptchaSolver

solver = CaptchaSolver(driver=<selenium_driver>).setCaptchaTypeAsRecatpchaV2()
solver.solve()
# Note: you can also set driver later using solver.driver = driver
# To get a working example, use testcase
```
- Still not enough: use `CaptchaSolver` as *parent* class to *your* class and define your `new_captcha(self)` method. 
                    You'll have temporary storage managed my CaptchaSolver, and many more advantages

## TokenSolver
TODO
## TestCases
Testcase module is in api directory

To start testing out captcha solving, use command `py -m api.testcase`
#### Arguments:
- headless1: run the driver in headless way
- headless2: run the driver in new headless way using `headless=new` option
- no_of_tests: no of tests to perform
- test: This can be 1, 2, 3 or 4 depending on task as explained below

1. recaptcha_v2

2. recaptcha_v2 on custom frame

3. hcaptcha

4. hcaptcha on custom frame"

# Token Solver

This is the flask app used to get token of desired captcha so that it can be injected to bypass captcha anytime anywhere


## Endpoints
- `http://127.0.0.1:5004`
- `http://0.0.0.0:5004`

## Sample request

1. Send http request on: `endpoint/submit`
2. Sample data: `{'type': 'recaptcha', 'domain': 'nopecha.com', 'sitekey': '6Ld8NA8jAAAAAPJ_ahIPVIMc0C4q58rntFkopFiA', 'timeout': 300}`
3. Loop over `endpoint/response` to get token as soon as it is processed

### Payloads
- hCaptcha: `{'type': 'hcaptcha', 'domain': 'nopecha.com', 'sitekey': 'b4c45857-0e23-48e6-9017-e28fff99ffb2', 'timeout': 300}`
- reCaptcha: `{'type': 'recaptcha', 'domain': 'nopecha.com', 'sitekey': '6Ld8NA8jAAAAAPJ_ahIPVIMc0C4q58rntFkopFiA', 'timeout': 300}`
#### Arguments
- type: Determines the type of captcha to be solved
- domain: Domain of target website
- sitekey: Sitekey of target website
- timeout: Maximum time allowed to solve captcha otherwise return TimeoutException
- proxy: Proxy to use `(USER:PASS@IP:PORT)`
- visibility: Whether to see solving captcha or not, headless or normal `Default: False` means do not show browser
- enforcer: Launch multiple instances trying to solve the same captcha and whenever the captcha solves, eliminates all instance, it will increase
            resource consumption as multiple browser spawned at a time, its value is integer, `Default: 1`

# Contact
For any question about CaptchaXpert, feel free to contact me here

- Discord: https://discord.gg/BCfVDE4sv3
- Email: imuhammadzubair223@gmail.com
