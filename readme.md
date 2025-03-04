# Resume Builder

This software is meant to be a free alternative to the standard paid AI Resume builders. The trade-off, at this current point in time, is that the LLM and BERT models are run locally. So, this requires a decent computer for good results. The general bare-minimum requirements are as follows
- 671b parameters ~1342GB total system RAM
- 70b parameters ~32.7GB total system RAM
- 32b parameters ~14.9GB total system RAM
- 14b parameters ~6.5GB total system RAM
- 8b parameters ~3.7GB total system RAM
- 7b parameters ~3.3GB total system RAM
- 1.5b paremeters ~700MB total system RAM

While these are the minimums for total system RAM, the software will run much quicker if these numbers correlate to your GPU VRAM instead. If you choose (in the settings below) a model size that is too large for your computer, *the software will default to the largest model your computer can handle*. If this is what you want, just set the model to `'671b'` in your settings (see below)

For ARM-based MacOS systems, the total system RAM is affectively your GPU RAM, since it has unified memory. My 64GB M1 Max Macbook can easily run the `'32b'` model.

### How it works

---

The software utilizes some softwares that will need to be installed by the user.

#### Ollama
The first major one is Ollama. Ollama is utilized to download models locally and run them through the Python script. 
Simply go to the [Ollama download page](https://ollama.com/download) and download the version that matches your operating system.


#### WKHTMLtoPDF
The second software, which is used for creating the PDF Resume/CV and Cover Letters, is the WK HTML to PDF software. Go the the [wkhtmltopdf downloads page](https://wkhtmltopdf.org/downloads.html) and install the correct version for your operating system.

Unlike Ollama, you will need to add the installed `/bin` folder to your system PATH. This is because the software directly calls the executable to run the conversion of the HTML version of the resume to PDF.

For Windows operating systems, this bin is located at `C:\Program Files\wkhtmltopdf\bin`.

#### Python Requirements

Once the previous softwares are installed, next will be adding the required Python packages from the `requirements.txt` included with this softare. To install the requirements (hopefully after you've created a virtual environment on your computer), navigate to the directory within which these scripts are stored in Terminal and then run the command 

`pip install -r requirements.txt`

#### Preparing the 'masterlist.json' file

In the directory you choose, you need to have a 'masterlist' of your resume in JSON form. An example of the structure is included in the install named `masterlist_example.json`. This exact structure is necessary for the software to be able to parse the incoming data and push it to the LLM. Once you've completely filled out your 'masterlist.json' file, we can finally run the script.

#### Running the code

Navigate to the file `ResumeBuilder-nonGUI.py`. Open the file and scroll down to the bottom. You'll notice a section under some code that says `if __name__ == "__main__":`. Under this snipped is where you'll set the correct values to run the script. The top half has inputs that are allowed and what they do, represented as:
```python
##### Required info for class

    # Where the save the output files [For testing, just use this directory]
    save_directory      = os.path.dirname( os.path.abspath( __file__ ) )

    # Path to the masterlist.json file for my base resume [use the _small.json for testing]
    master_list         = os.path.join( save_directory, "masterlist_example_small.json" )

    # How many bullet points to keep under each job experience
    bullet_points_per   = 5

    # The Deepseek model to use for the bullet point processing.
    # Options are 1.5, 7, 8, 14, 32, 70, and 671.
    # Larger = better. BUT, this is limited by your PC. If your PC can't handle the model you chose,
    # the software will choose the biggest model that your PC can handle.
    bullet_model        = "32"

    # Whether or not to generate a cover letter (some jobs require it)
    # Honestly, this kind of sucks. Maybe set this to false. Lol!
    cover_letter        = False

    # The Deepseek model to use for the cover letter, if chosen.
    # Options are 1.5, 7, 8, 14, 32, 70, and 671.
    # Larger = better. BUT, this is limited by your PC. If your PC can't handle the model you chose,
    # the software will choose the biggest model that your PC can handle.
    cover_letter_model  = '32'

    # Whether or not the generate a CV style resume (includes Patents, Publications, and Presenations)
    cv_style            = True

    # Whether or not to include the summary at the top of the resume
    include_summary     = True
```

Fill these out with the settings that you want. After this, we need the information for the job posting. This is below this component and labeled as:

```python
    ################## FILL OUT THIS PART ##################

    # What the title is for the job you're applying to. (i.e. Executive Director of Candy)
    job_title           = "Senior Cookie Eater"

    # The name of the company you're applying to (i.e. Willy Wonka's Chocolate Factory)
    job_company_name    = "Cool Company name"

    # The description of the job posted
    job_description     = """
    Some job description
    """

    ################## END OF: FILL OUT THIS PART ##################
```

Finally, save the document and run the script.

The first time this runs, it will take quite a while due to it first analyzing your master list. After the first time, it should go much faster. 

After the first run, I highly recommend looking at the new remodeled master list saved in your directory. Look at each bullet point under your experience and ensure that the values make sense. As this is a small local LLM making the bullet points, it will make a lot of mistakes that will need to be corrected.

When you're satisfied with the edits you've made, re-run the code and it will utilize the edits you've made to make a final version of the Resume. You should only need to do this once, as the customization of the resume for each job posting comes from sentiment analysis of your masterlist versus the job posting.

#### Custom Designed Resumes

Under the `/css` directory, you will find a bare `css/resume.css` file. For custom designs, you can edit this CSS file. The software saves an HTML version of your resume in the `/resumes` directory. You can utilize this file, along with the `css/resume.css` file to see what your designs looks like before re-running the script. Once you have a design that you like, simply re-run the script and your newly designed version will be saved.
