import datetime
import os
import platform
import re
from multiprocessing.pool import Pool

import requests
from bs4 import BeautifulSoup

import generateDailyMaster

today = str(datetime.datetime.today().strftime('%Y-%m-%d'))


def removeSpecial(inputString):
    return re.sub(r'[^a-zA-Z0-9]+', '', inputString)


todayFolder = os.getcwd() + today


def createTodayFolder():
    os.getcwd()
    if not os.path.exists(todayFolder):
        os.makedirs(todayFolder)


def writeToCSV(filename, csvContents):
    if platform.system() == 'Linux':
        file_to_write = todayFolder + "/" + filename
    else:
        file_to_write = todayFolder + "\\" + filename

    if (len(csvContents) > 0):
        with open(file_to_write, 'w') as f:
            for csv_line in csvContents:
                f.write(csv_line + "\n")


def findIrishJobs(job, type):
    csvContents = []
    baseurl = "https://www.irishjobs.ie"
    url = baseurl + "/ShowResults.aspx?Keywords=" + job + type
    result = requests.get(url)
    soup = BeautifulSoup(result.content, "html.parser")
    titles = soup.find_all("div", {"class": re.compile(r"module job-result")})

    for title in titles:
        job_result = ""
        job_and_company = title.contents[1].contents[3].text.replace("\n\n\n", " ").replace("\n\n", "")

        company = title.contents[1].contents[3].text.split("\n\n\n")[2].split("\n")[0]

        if "company reviews" in job_and_company:
            job_and_company = job_and_company.split("company reviews")
            job_result = job_and_company[0].split("company reviews")[0].split(company)[0]
        else:
            if ("\n" in job_and_company):
                job_and_company.split("\n")[0].replace(company, "")
            else:
                job_result = job_and_company.replace(company, "")

        csv_line = str(removeSpecial(job_result)) + "," + str(company) + ", " + baseurl + \
                   title.contents[1].contents[9].contents[3].attrs['href']
        if (csv_line not in csvContents):
            csvContents.append(csv_line)

    outputFile = "irishJob" + job + today + ".csv"
    writeToCSV(outputFile, csvContents)


def findIndeed(job):
    page_number = 0
    csv_contents = []

    while page_number < 100:
        url = "https://ie.indeed.com/jobs?q={{ROLE}}&l={{LOCATION}}" + "&start={{START}}"
        url = url.replace("{{ROLE}}", job).replace("{{LOCATION}}", "Dublin")
        url = url.replace("{{START}}", str(page_number))
        result = requests.get(url)
        soup = BeautifulSoup(result.content, "html.parser")

        titles = soup.find_all("div", {"class": re.compile(r"company")})
        for title in titles:
            name = re.sub(r'([^\s\w]|_)+', '', str(str(title.text.split(" ")[8:]).split("\\")[:1]))
            role = re.sub(r'([^\s\w]|_)+', '', str(title.parent.text.split("\n")[2]))
            job_url = url + "&vjk=" + title.parent.attrs['data-jk']
            csv_line = role + ", " + name + " , " + job_url

            if csv_line not in csv_contents:
                csv_contents.append(csv_line)
        page_number += 10

    outputFile = "indeed" + job + today + ".csv"
    writeToCSV(outputFile, csv_contents)


def create_pool(jobs, irishJobsAgency, irishJobsRecruiter):
    pool = Pool(processes=8)
    pool.starmap(findIrishJobs, zip(jobs, irishJobsRecruiter))
    pool.starmap(findIrishJobs, zip(jobs, irishJobsAgency))
    pool.map(findIndeed, jobs)
    pool.close()
    pool.join()


def main():
    jobs = ["java+developer", "junior+java+developer", "junior+android+developer", "android+developer",
            "junior+ios+developer", "ios+developer", "junior+devops", "devops", "junior+.net+developer",
            ".net+developer",
            "junior+full+stack", "full+stack", "junior+ai+software+engineer",
            "ai+software+engineer", "junior+web+developer", "web+developer", "junior+data+scientist", "data+scientist",
            "junior+scrum+master", "scrum+master"]

    irishJobsRecruiter = "&autosuggestEndpoint=%2Fautosuggest&Location=102&Category=3&Recruiter=Company&btnSubmit=+irishJobs-companies"
    irishJobsAgency = "&autosuggestEndpoint=%2Fautosuggest&Location=102&Category=3&Recruiter=Agency&btnSubmit=+irishJobs-agency"

    createTodayFolder()
    print("START : " + str(datetime.datetime.now()))
    create_pool(jobs, irishJobsAgency, irishJobsRecruiter)
    print("END : " + str(datetime.datetime.now()))

    generateDailyMaster.createDailyMasterFile()


if __name__ == '__main__':
    main()