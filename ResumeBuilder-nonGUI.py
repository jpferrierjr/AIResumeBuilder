'''

    Title:          Resume Builder

    Description:    This class takes the resume information from a masterlist.json and fully builds out a resume for a given job posting.
                    This is the non-GUI version for easy early use.

    Author:         Dr. John Ferrier

    Date:           27 February 2025

'''


import os
import json
import errno
import pdfkit
#from txt2pdf.core import txt2pdf
from urllib.parse import urlsplit
from SkillsBERT import BERTSkills
from BulletBERT import BERTBullets
from ProjectsBERT import BERTProjects
from BulletRebuilder import BulletRebuilder


class ResumeBuilder:

    def __init__( self,
                masterlist:str      = os.path.join( os.path.dirname(os.path.abspath(__file__)), "masterlist.json" ),
                bullets_per:int     = 5,
                skills_per:int      = 5,
                projects_per:int    = 5,
                bl_model:str        = "32",
                cover_letter:bool   = False,
                cl_model:str        = "32",
                cv_style:bool       = False,
                job_title:str       = "",
                job_company:str     = "",
                job_desc:str        = "",
                resume_css:str      = os.path.join( os.path.dirname(os.path.abspath(__file__)), 'css', 'resume.css'),
                save_dir:str        = os.path.dirname(os.path.abspath(__file__)),
                force_rebuilds      = False,
                include_summary     = True ):
        
        # Set self variables
        self.masterlist     = masterlist
        self.bullets_per    = bullets_per
        self.skills_per     = skills_per
        self.projects_per   = projects_per
        self.bl_model       = bl_model
        self.cover_letter   = cover_letter
        self.cl_model       = cl_model
        self.cv_style       = cv_style
        self.job_title      = job_title
        self.job_company    = job_company
        self.job_desc       = job_desc
        self.resume_css     = resume_css
        self.force_rebuilds = force_rebuilds
        self.save_dir       = save_dir
        self.include_sum    = include_summary
        self.CL_html_file   = None

        # Bare variables for use later
        self.remastered_json    = ""
        self.remastered_list    = ""
        self.parsed_bullets     = []
        self.BR_save_dir        = os.path.join( self.save_dir, "masterlist_rebuilds" )
        self.BB_save_dir        = os.path.join( self.save_dir, "BERT_rebuilds" )
        self.resume_save_dir    = os.path.join( self.save_dir, "resumes" )
        self.cl_save_dir        = os.path.join( self.save_dir, "cover_letters" )

        # Check that the new save directories exist. If not, build them
        if not os.path.exists( self.BR_save_dir ):
            os.mkdir( self.BR_save_dir )
        if not os.path.exists( self.BB_save_dir ):
            os.mkdir( self.BB_save_dir )
        if not os.path.exists( self.resume_save_dir ):
            os.mkdir( self.resume_save_dir )
        if not os.path.exists( self.cl_save_dir ):
            os.mkdir( self.cl_save_dir )

        # Look for the masterlist. If it doesn't exist, raise an exception and quit the software
        if not os.path.isfile( self.masterlist ):
            raise FileNotFoundError( errno.ENOENT, os.strerror(errno.ENOENT), self.masterlist )
        
        # We can just continue, as the bulletRebuilder will open it.
        
    # DONE: Processes all necessary models for the resume rebuild for the job application 
    def process( self ):

        print( "###### STARTING Bullet Rebuilder" )

        # Start the bullet rebuilder
        BR  = BulletRebuilder(  master_file     = self.masterlist,
                                force_rebuild   = self.force_rebuilds, 
                                modelSize       = self.bl_model,
                                save_directory  = self.BR_save_dir )
        
        print( "###### PROCESSING Bullets with Bullet Rebuilder" )
        # Process the bullet points to build the remodeled masterlist.
        # If this has already been run, it will return the previously saved modeled data to reduce computation.
        BR.process()

        # Also build and save a new summary
        if self.include_sum:
            self.summary    = BR.buildSummary( job_title = self.job_title, job_company = self.job_company, job_description = self.job_desc )
            print( f"{self.summary=}" )

        # New file will be saved at BR.master_modeled. This will be used for the BERT model
        self.remastered_json    = BR.master_modeled
        self.remastered_list    = BR.master_list

        print( "###### Bullet Rebuilder COMPLETE!" )
        
        
        # Parse the accomplishments for BERT modeling. This NEEDS to be done by explicitly opening the parsing the new JSON file.
        # This is done to help avoid rewriting a lot of the older code, keeping processes segregated
        self.parseNewMasterlistForBERT()

        print( "###### STARTING Bullet BERT Processor" )
        # Now, let's send the parsed_bullets to the BERT model and render to get the new bullet points for our resume
        BB = BERTBullets( jobTitle      = self.job_title, 
                         jobCompany     = self.job_company, 
                         jobDesc        = self.job_desc, 
                         bulletPoints   = self.parsed_bullets,
                         minPoints      = self.bullets_per, 
                         save_location  = self.BB_save_dir,
                         force_rebuild  = self.force_rebuilds )
        
        print( "###### PROCESSING Bullets with Bullet BERT Processor" )
        self.resume_bullets     = BB.render()
        print( "###### Bullet BERT Processor COMPLETE!" )

        skills      = self.remastered_list['skills']
        subskills   = self.remastered_list['subskills']

        print( "###### STARTING Top Skills BERT Processor" )
        BS  = BERTSkills(   skills              = skills, 
                            subskills           = subskills,
                            job_title           = self.job_title, 
                            job_description     = self.job_desc,
                            count               = self.skills_per )

        print( "###### PROCESSING Top Skills BERT Processor" )
        self.resume_skills      = BS.render()
        print( "###### Top Skills BERT Processor COMPLETE!" )


        print( "###### STARTING Projects BERT Processor" )
        ### Choose the projects
        projects    = self.remastered_list['projects']
        BP  = BERTProjects( job_description = self.job_desc, 
                            projects        = projects, 
                            count           = self.projects_per )
        print( "###### PROCESSING Projects BERT Processor" )
        # List of dictionary {"title": "", "link": "", "description": ""}
        self.chosen_projects = BP.render()
        print( "###### Projects BERT Processor COMPLETE!" )

        # FINALLY, create a cover letter
        if self.cover_letter:
            print( "###### Generating Cover Letter" )
            _, CL_html_file  = BR.buildCoverLetter(job_title = self.job_title, job_company = self.job_company, job_description = self.job_desc, save_dir = self.cl_save_dir)

            # Save the html file to pdf
            CL_pdf_file     = CL_html_file[:-5] + ".pdf"
            self.html_to_pdf( html_file_name = CL_html_file, pdf_file_name = CL_pdf_file )
            print( "###### Cover Letter Generated!" )

        # Save the reults automatically
        self.savedocs()

    # DONE: Parses the new masterlist from DeepSeek to be used for the BERT modeler for job comparisons
    def parseNewMasterlistForBERT( self ):

        # Open the remodeled master list
        # Check if masterlist exists
        if not os.path.isfile(self.remastered_json):
            raise FileNotFoundError( errno.ENOENT, os.strerror(errno.ENOENT), self.remastered_json )

        # Check that it is JSON format
        if not self.remastered_json.lower().endswith( ".json" ):
            raise ValueError("Unsupported file type. Only .json files are allowed.")
        
        # Continue parsing
        with open(self.remastered_json, 'r') as file:
            self.mList = json.load( file )

        # Parse experiences into self.bullets_lists. FORMAT: { 'type':1, 'title':'job_title', 'bullets':[] }
        for v in self.mList['experiences']:

            # Cycle through each accomplishment
            self.parsed_bullets.append( { 'type':1, 'title':v['jobtitle'], 'bullets':v['projects'] } )
            
    # DONE: Parses all data to a markdown resume format
    def parseToMarkdown( self ):
        
        markdown_text   = ""

        #### All resumes/CV will have a header (info about you), education, experience, projects, and top skills for the job
        #### CVs will have the added publications, presentations, patents, 

        # Create header for resume
        # Add name, job title, email, location, linkedin, website

        # NOTE: This will look weird, due to the needs of formatting for the markdown file

        markdown_text   += f"# {self.remastered_list['about']['name']}\n"
        markdown_text   += f"## {self.job_title}\n"
        markdown_text   += f"#### {self.remastered_list['about']['email']}\n"
        markdown_text   += f"#### {self.remastered_list['about']['location']}\n"

        if not self.remastered_list['about']['website'] == "":
            split_website   = urlsplit(self.remastered_list['about']['website'])
            markdown_text += f"#### [{split_website.netloc}]({self.remastered_list['about']['website']})\n"

        if not self.remastered_list['about']['linkedin'] == "":
            markdown_text += f"#### [LinkedIn]({self.remastered_list['about']['linkedin']})\n"

        if not self.remastered_list['about']['github'] == "":
            markdown_text += f"#### [Github]({self.remastered_list['about']['github']})\n"



        #----- Build Summary
        if self.include_sum:
            markdown_text += "---\n"
            markdown_text += "## Summary\n"
            markdown_text += f"#### {self.summary}\n"""


        #----- Build Relevant Skills
        if len(self.resume_skills) > 0:
            skills_list = [ sk['skill'] for sk in self.resume_skills ]
            markdown_text += "---\n"
            markdown_text += "## Relevant Skills\n"
            markdown_text += f"{" | ".join(skills_list)}\n"


        #----- Build Education - This should also include certifications
        markdown_text += "## Education\n"

        for edu in self.remastered_list['education']:

            # Add basic education information
            markdown_text += f"### {edu['school']}\n"
            markdown_text += f"#### {edu['degree']}\n"

            # Add minor, if exists
            if not edu['minor'] == "":
                markdown_text += f"Minor: {edu['minor']}\n"

            # Add start/end date
            markdown_text += f"{edu['start-date']} - {edu['end-date']}\n"
            
            # Add thesis, if exists
            if not edu['thesis'] == "":
                markdown_text += f"Thesis: *{edu['thesis']}*\n"



        #----- Build Experience - This better actually exist. lol
        markdown_text += "## Experience\n"

        # Cycle through the experiences in the master list
        for i, exp in enumerate( self.remastered_list['experiences'] ):

            markdown_text += f"### {exp['company']}, {exp['jobtitle']}\n"
            markdown_text += f"#### {exp['start']} - {exp['end']}\n"

            # Add the accomplishments that have been computed
            for acc in self.resume_bullets[i]['bullets']:
                
                markdown_text += f"- {acc['description']}\n"


        #----- Build Projects
        if len( self.chosen_projects ) > 0:
            markdown_text += "## Projects\n"

            for proj in self.chosen_projects:

                if not proj['link'] == "":
                    markdown_text += f"### [{proj['title']}]({proj['link']})\n"
                else:
                    markdown_text += f"### {proj['title']}\n"

                markdown_text += f"{proj['description']}\n"

        # If CV style, add Publications, Presentations, and Patents, Outreach
        if self.cv_style:
            #----- Build Publications
            if len(self.remastered_list['publications']) > 0:
                markdown_text += "## Publications\n"

                for i, pub in enumerate( self.remastered_list['publications'] ):

                    # Split the authors and only put the first 3.
                    authors_split   = pub['authors'].split(";")
                    authors         = ",".join( authors_split[:2] )

                    authors_split   = authors.split(",")
                    authors         = ",".join( authors_split[:2] )

                    markdown_text += f"{i+1}. {authors}. *{pub['title']}*. {pub['journal']}. ({pub['year']}). {pub['volume']}. {pub['page_range']}. [DOI: {pub['DOI']}](https://doi.org/{pub['DOI']})\n"

            #----- Build Presentations
            if len(self.remastered_list['presentations']) > 0:
                markdown_text += "## Presentations\n"

                for i, pres in enumerate( self.remastered_list['presentations'] ):

                    # Split the authors and only put the first 3.
                    authors_split   = pres['authors'].split(";")
                    authors         = ",".join( authors_split[:2] )
                    authors_split   = authors.split(",")
                    authors         = ",".join( authors_split[:2] )

                    title           = f"{pres['title']}"

                    if not pres['link'] == "":
                        title   = f"[{pres['title']}]({pres['link']})"

                    markdown_text += f"{i+1}. {authors}. *{title}*. {pres['event']}. ({pres['date']})\n"


            #----- Build Patents
            if len(self.remastered_list['patents']) > 0:
                markdown_text += "## Patents"

                for i, pat in enumerate( self.remastered_list['patents'] ):

                    title   = f"{pat['title']}"

                    if not pat['link'] == "":
                        title   = f"[{pat['title']}]({pat['link']})"

                    markdown_text += f"{i+1}. *{title}*. Patent Number: {pat['patent_number']}\n"

            
            #----- Build Outreach
            if len(self.remastered_list['outreach']) > 0:
                markdown_text += "## Outreach\n"

                for out in self.remastered_list['outreach']:

                    title   = f"{out['title']}"

                    # Add later
                    # if not out['link'] == "":
                    #     title   = f"[{out['title']}]({out['link']})"

                    markdown_text += f"### {title}\n"
                    markdown_text += f"*{out['organization']}*\n"
                    markdown_text += f"{out['description']}\n"


        #----- Build Awards
        if len(self.remastered_list['awards']) > 0:
            markdown_text += "## Awards\n"

            for award in self.remastered_list['awards']:
                if not award['link'] == "":
                    markdown_text += f"### [{award['award']}]({award['link']})\n"
                else:
                    markdown_text += f"### {award['award']}\n"
                markdown_text += f"#### {award['organization']}\n"
                markdown_text += f"{award['description']}\n"

        return markdown_text
    
    # DONE: Parses all data to a markdown resume format
    def parseToHTML( self ):
        
        html_text   = "<!DOCTYPE html><html><head><title>Resume</title>"
        
        # Check for CSS and add it to the head
        if self.resume_css is not None:
            if os.path.exists( self.resume_css ):
                with open(self.resume_css, 'r') as file:
                    css = file.read()
                html_text += f"<style>{css}</style>"
            
        html_text += "</head><body>"   

        #### All resumes/CV will have a header (info about you), education, experience, projects, and top skills for the job
        #### CVs will have the added publications, presentations, patents, 

        # Create header for resume
        # Add name, job title, email, location, linkedin, website

        # NOTE: This will look weird, due to the needs of formatting for the markdown file

        html_text   += "<div class='about'>"

        html_text   += f"<h1>{self.remastered_list['about']['name']}</h1>"
        html_text   += f"<h2>{self.job_title}</h2>"
        html_text   += f"<h4>{self.remastered_list['about']['email']}<h4>"
        html_text   += f"<h4>{self.remastered_list['about']['location']}<h4>"

        if not self.remastered_list['about']['website'] == "":
            split_website   = urlsplit(self.remastered_list['about']['website'])
            html_text += f"<h4><a href='{self.remastered_list['about']['website']}' target='_blank'>{split_website.netloc}</a></h4>"

        if not self.remastered_list['about']['linkedin'] == "":
            html_text += f"<h4><a href='{self.remastered_list['about']['linkedin']}' target='_blank'>LinkedIn</a></h4>"

        if not self.remastered_list['about']['github'] == "":
            html_text += f"<h4><a href='{self.remastered_list['about']['github']}' target='_blank'>Github</a></h4>"

        html_text   += "</div>"

        #----- Build Summary
        if self.include_sum:
            html_text += "<hr /><div class='summary_container'>"
            html_text += "<h2>Summary</h2>"
            html_text += f"<div class='summary'>{self.summary}</div></div>"


        #----- Build Relevant Skills
        if len(self.resume_skills) > 0:
            skills_list = [ sk['skill'] for sk in self.resume_skills ]
            html_text += "<hr /><div class='skills_container'>"
            html_text += "<h2>Relevant Skills</h2>"
            html_text += f"<div class='skills'>{" | ".join(skills_list)}</div></div>"


        #----- Build Education - This should also include certifications
        html_text += "<h2>Education</h2>"

        for edu in self.remastered_list['education']:

            # Add basic education information
            html_text += f"<div class='education'><h3>{edu['school']}</h3>"
            html_text += f"<h4>{edu['degree']}</h4>"

            # Add minor, if exists
            if not edu['minor'] == "":
                html_text += f"<div class='education_minor'>Minor: {edu['minor']}</div>"

            # Add start/end date
            html_text += f"<div class='education_dates'>{edu['start-date']} - {edu['end-date']}</div>"
            
            # Add thesis, if exists
            if not edu['thesis'] == "":
                html_text += f"<div class='education_thesis' style='font-style: italic;'>Thesis: {edu['thesis']}</div>"

            # Close out 'education_container'
            html_text   += "</div>"



        #----- Build Experience - This better actually exist. lol
        html_text += "<div class='experience_container'><h2>Experience</h2>"

        # Cycle through the experiences in the master list
        for i, exp in enumerate( self.remastered_list['experiences'] ):

            html_text += f"<div class='experience'><h3>{exp['company']} - {exp['jobtitle']}</h3>"
            html_text += f"<div class='experience_dates'>{exp['start']} - {exp['end']}</div><ul class='experience_list'>"

            # Add the accomplishments that have been computed
            for acc in self.resume_bullets[i]['bullets']:
                
                html_text += f"<li>{acc['description']}</li>"

            # End unordered list and 'experience' div
            html_text   += "</ul></div>"
        
        # End 'experience_container'
        html_text   += "</div>"

        #----- Build Projects
        if len( self.chosen_projects ) > 0:
            html_text += "<div class='projects_container'><h2>Projects</h2>"

            for proj in self.chosen_projects:
                # Start 'projects' div
                html_text   += "<div class='projects'>"

                if not proj['link'] == "":
                    html_text += f"<h3><a href='{proj['link']}' target='_blank'>{proj['title']}</a></h3>"
                else:
                    html_text += f"<h3>{proj['title']}</h3>"

                html_text += f"<div class='project_description'>{proj['description']}</div>"

                # End 'projects' div
                html_text   += "</div>"

            # end 'projects_container' div
            html_text   += "</div>"

        # If CV style, add Publications, Presentations, and Patents, Outreach
        if self.cv_style:
            #----- Build Publications
            if len(self.remastered_list['publications']) > 0:
                html_text += "<div class='publications_container'><h2>Publications</h2>"

                # Start ordered list
                html_text += "<ol class='publications_list'>"
                for pub in self.remastered_list['publications']:

                    # Split the authors and only put the first 3.
                    authors_split   = pub['authors'].split(";")
                    authors         = ",".join( authors_split[:2] )

                    authors_split   = authors.split(",")
                    authors         = ",".join( authors_split[:2] )

                    html_text += f"<li>{authors}. <span style='font-style: italic;'>{pub['title']}</span>. {pub['journal']}. ({pub['year']}). {pub['volume']}. {pub['page_range']}. <a href='https://doi.org/{pub['DOI']}' target='_blank'>DOI: {pub['DOI']}</a></li>"

                # End ordered list and 'publications_container' div
                html_text   += "</ol></div>"

            #----- Build Presentations
            if len(self.remastered_list['presentations']) > 0:
                html_text   += "<div class='presentations_container'><h2>Presentations</h2>"

                # Start ordered list
                html_text   += "<ol class='presentations_list'>"

                for pres in self.remastered_list['presentations']:

                    # Split the authors and only put the first 3.
                    authors_split   = pres['authors'].split(";")
                    authors         = ",".join( authors_split[:2] )
                    authors_split   = authors.split(",")
                    authors         = ",".join( authors_split[:2] )

                    title           = f"{pres['title']}"

                    if not pres['link'] == "":
                        title   = f"<a href='{pres['link']}' target='_blank'>{pres['title']}</a>"

                    html_text += f"<li> {authors}. <span style='font-style: italic;'>{title}</span>. {pres['event']}. ({pres['date']})</li>"

                # End ordered list and 'presentations_container' div
                html_text   += "</ol></div>"


            #----- Build Patents
            if len(self.remastered_list['patents']) > 0:
                html_text   += "<div class='patents_container'><h2>Patents</h2>"

                # Start ordered list
                html_text   += "<ol class='patents_list'>"

                for pat in self.remastered_list['patents']:

                    title   = f"{pat['title']}"

                    if not pat['link'] == "":
                        title   = f"<a href='{pat['link']}' target='_blank'>{pat['title']}</a>"

                    html_text += f"<li><span style='font-style: italic;'>{title}</span>. Patent Number: {pat['patent_number']}</li>"

                # End ordered list and 'patents_container' div
                html_text   += "</ol></div>"

            
            #----- Build Outreach
            if len(self.remastered_list['outreach']) > 0:
                html_text += "<div class='outreach_container'><h2>Outreach</h2>"

                for out in self.remastered_list['outreach']:

                    # Start outreach div
                    html_text   += "<div class='outreach'>"

                    title       = f"{out['title']}"

                    # Add later
                    # if not out['link'] == "":
                    #     title   = f"[{out['title']}]({out['link']})"

                    html_text   += f"<h3>{title}</h3>"
                    html_text   += f"<div class='outreach_organization'>{out['group']}</div>"
                    html_text   += f"<div class='outreach_description'>{out['description']}</div>"

                    # close outreach div
                    html_text   += "</div>"

                # close 'outreach_container' div
                html_text   += "</div>"


        #----- Build Awards
        if len(self.remastered_list['awards']) > 0:
            html_text += "<div class='awards_container'><h2>Awards</h2>"

            for award in self.remastered_list['awards']:

                # start awards div
                html_text   += f"<div class='awards'>"
                
                if not award['link'] == "":
                    html_text   += f"<h3><a href='{award['link']}' target='_blank'>{award['award']}</a></h3>"
                else:
                    html_text   += f"<h3>{award['award']}</h3>"
                   
                html_text   += f"<h4>{award['organization']}</h4>"
                html_text   += f"<div class='awards_description'>{award['description']}</div>"

                # close awards div
                html_text   += "</div>"

            # close 'awards_container' div
            html_text   += "</div>"

        # close body and html
        html_text   += "</body></html>"

        return html_text

    # DONE: Saves the resultant resume documents, to include the markdown and PDF versions
    def savedocs( self ):

        #print( "Building a new Markdown Resume..." )
        print( "Building a new HTML Resume..." )

        #### Build file names
        # the base name should have your last name, the job title, and the company name (at least the first component)
        lastname            = self.remastered_list['about']['name'].split()[-1]
        jobTitle            = "".join(self.job_title.split())
        comp_name           = self.job_company.split()[0]
        basename            = f"{lastname}_{jobTitle.lower()}_{comp_name.lower()}"
        if self.cv_style:
            # Add CV to the basename
            basename += "_CV"
        else:
            basename += "Resume"

        self.markdown_filename  = os.path.join( self.resume_save_dir, f"{basename}.md" )
        self.html_filename      = os.path.join( self.resume_save_dir, f"{basename}.html" )
        self.pdf_filename       = os.path.join( self.resume_save_dir, f"{basename}.pdf" )

        # Save the markdown language model
        #md_format           = self.parseToMarkdown()
        html_format         = self.parseToHTML()

        # with open(  self.markdown_filename, "w" ) as file:
        #     file.write( md_format )

        with open( self.html_filename, "w" ) as file:
            file.write( html_format )

        #print( "Markdown Resume Complete!" )
        print( "HTML Resume Complete!" )
        
        # Putting the PDF creation into another function for ease of use if mistakes are made
        #self.savePDF( pdf_file_name = self.pdf_filename, markdown_file_name = self.markdown_filename )
        self.html_to_pdf( html_file_name = self.html_filename, pdf_file_name = self.pdf_filename )

    # DONE: Saves a PDF version of the markdown file
    def savePDF( self, pdf_file_name = "", markdown_file_name = "" ):

        print( "Building a new PDF Resume..." )
        # Save the PDF version with CSS (if specified)
        CSS_file            = None
        if self.resume_css is not None:
            if os.path.exists( self.resume_css ):
                CSS_file    = self.resume_css
        
        # Use txt2pdf to save us from having to rewrite a bunch of code.
        # txt2pdf(    pdf_file_path   = pdf_file_name,
        #            md_file_path    = markdown_file_name,
        #            css_file_path   = CSS_file )
        
        print( "PDF Resume Complete!" )
    
    def html_to_pdf( self, html_file_name = "", pdf_file_name = ""):
        """
        Converts an HTML file to a PDF file, respecting CSS.

        Args:
            html_file (str): Path to the input HTML file.
            pdf_file (str): Path to the output PDF file.
        """
        try:
            # Check if wkhtmltopdf is installed and in PATH.
            # pdfkit relies on wkhtmltopdf for the actual conversion.
            #config = pdfkit.configuration( wkhtmltopdf ='wkhtmltopdf' )
            #config = pdfkit.configuration( wkhtmltopdf = os.environ.get( 'Path', 'wkhtmltopdf' ) )

            # Options to handle CSS and other rendering aspects.
            options = {
                'page-size': 'Letter',
                'margin-top': '0.75in',
                'margin-right': '0.75in',
                'margin-bottom': '0.75in',
                'margin-left': '0.75in',
                'encoding': "UTF-8",
                'quiet': '', # Suppress wkhtmltopdf output
            }
            if self.resume_css is not None:
                if os.path.exists( self.resume_css ):
                    pdfkit.from_file( html_file_name, pdf_file_name, options = options, css = self.resume_css ) #configuration = config, 
                else:
                    pdfkit.from_file( html_file_name, pdf_file_name, options = options )
            else:
                pdfkit.from_file( html_file_name, pdf_file_name, options = options )
                
            print( f"Successfully converted {html_file_name} to {pdf_file_name}" )

        except FileNotFoundError:
            print("Error: wkhtmltopdf not found. Please install it and ensure it's in your PATH.")
        except Exception as e:
            print(f"An error occurred: {e}")


if __name__ == "__main__":

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



    ################## FILL OUT THIS PART ##################


    #### This is a real job posting from: https://www.linkedin.com/jobs/collections/recommended/?currentJobId=4160905560

    # What the title is for the job you're applying to. (i.e. Executive Director of Candy)
    job_title           = "Senior Computational Physicist"

    # The name of the company you're applying to (i.e. Willy Wonka's Chocolate Factory)
    job_company_name    = "Lawrence Livermore National Laboratory"

    # The description of the job posted
    job_description     = """We have openings for Computational Physicists to pursue challenges relevant to national security in the development of multi-physics simulation codes. Under consultative direction you will collaborate as part of an interdisciplinary code development team in advancing the state of the art in large-scale multi-physics simulation. The national security mission involves developing simulation capabilities for Stockpile Stewardship, nuclear counter-terrorism, conventional weapons, and high energy density physics experiments. The code development focus is on models and algorithms for use in high-performance computing on the latest large-scale parallel computing platforms. You will act as a scientific/technical leader as part of large projects/programs, contribute to the development of innovative principles and ideas, will play a role in attracting and retaining projects, programs, and funding due to degree of technical expertise. These positions are in the Design Physics Division within the Strategic Deterrence Directorate.

These positions may offer a hybrid schedule, which includes the flexibility to work from home one or more days per week, after a probationary period. The specifics of the hybrid schedule, including the exact number of days required in the office and virtual work options may vary based on the needs of the team and the organization.

You will

Develop algorithms and simulation tools to advance the state of the art in multi-physics simulation for a large variety of physical processes in 2D and 3D, where problems are not well defined.
Independently develop and/or provide in-depth analysis of physics capabilities in support of a diverse user community using advanced simulation tools to solve highly complex problems that may not be well defined.
Provide advanced technical support, informal training, and guidance to code users in the application of simulation tools developed.
Collaborate in the development of simulation tools and direct/influence the strategy and technical direction of research activities as part of a multi-disciplinary team.
Present and disseminate advanced research results at scientific conferences and in peer-reviewed publications, in both open and classified environments, internal and external to LLNL.
Set broad technical strategies and/or direct multi-disciplinary teams to achieve program goals.
Perform other duties as assigned.

Qualifications

Ability to secure and maintain a U.S. DOE Q-level clearance which requires U.S. citizenship.
PhD in one or more of these specialized fields: physics, mathematics, engineering, or related field or the equivalent combination of education and related experience.
Subject matter expert knowledge of highly advanced concepts to include experience and ability to lead independent work in one or more science disciplines, such as shock hydrodynamics, fluid mechanics, material behavior, particle transport, radiation transport, plasma physics.
Significant experience evaluating algorithms and methods for their fitness for a particular task, as well as developing and implementing new numerical algorithms.
Significant experience developing and supporting and/or leading multi-dimensional numerical simulation and demonstrated analytical and conceptual skills and creativity.
Advanced programming experience/fluency in Python, FORTRAN, C and/or C++ and significant experience developing and implementing algorithms for massively-parallel computer architectures.
Effective verbal and written communication skills and experience authoring high-quality reports/publications and delivering effective technical presentations.
Significant experience working independently and in a team-research environment effectively.
Significant experience at the expert level in the development of principles, theories, concepts, and techniques relevant to applied physics research and experience converting theory into models or algorithms appropriate for numerical simulation."""

    
    
    
    ################## END OF: FILL OUT THIS PART ##################




    # Whether or not to force all models to rebuild what they have already processed.
    # Marking this as True will make the process take much longer! Beware of this!
    force_rebuilds      = False

    # Initialize the class
    RB  = ResumeBuilder( masterlist     = master_list, 
                        bullets_per     = bullet_points_per,
                        bl_model        = bullet_model,
                        cover_letter    = cover_letter,
                        cl_model        = cover_letter_model,
                        cv_style        = cv_style,
                        job_title       = job_title,
                        job_company     = job_company_name,
                        job_desc        = job_description,
                        force_rebuilds  = force_rebuilds,
                        save_dir        = save_directory,
                        include_summary = include_summary )
    # Process the bullets, cover letter, and job posting to build a resume/CV
    RB.process()

    #### If the resume wording isn't to your liking, simply edit the new masterlist_{modelsize}b.json to show what you want.
    #### and then rerun
    # RB.savedocs()
    
    #### If only the summary looks bad, rewrite the summary in the markdown file (the one that ends with .md)
    #### and then rerun
    # RB.savePDF( pdf_file_name = "/path/to/cool_name.pdf", markdown_file_name = "/path/to/markdown.md" )