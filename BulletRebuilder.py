'''

    Title:          Bullet Rebuilder

    Description:    This class opens a "master list" resume and rebuilds each bullet point within the file to better match what is expected from resume structures
                    for both ATS filtering and HR standards. This will typically take the quantitative form of `Accomplished X as measured by Y by doing Z`.

    Author:         Dr. John Ferrier

    Date:           16 February 2025

'''

# Import libraries
import os
import re
import sys
import json
import errno
from typing import Optional
import platform
import psutil
import GPUtil
from datetime import datetime
from ollama import chat, ChatResponse, ResponseError, pull
import ollama


class BulletRebuilder:

    '''
    
    '''
    # Initializer
    def __init__( self, master_file:str         = '', 
                force_rebuild:bool              = False, 
                modelSize:str                   = '32', 
                override_default_prompt:bool    = False, 
                prompt:str                      = '', 
                force_all_models:bool           = False,
                save_directory:str              = os.path.dirname(os.path.abspath(__file__)) ):
        
        # Input variables
        self.master_file    = master_file               # Location of master file (in markdown language)
        self.modelSize      = modelSize                 # Size of Deepseek R1 model to use. Default is R1:32b (for local use)
        self.modelSizeFloat = float(modelSize)          # Model chosen in float format (for analysis)
        self.force_rebuild  = force_rebuild             # Forces a rebuild of the master_file, if a rebuild is already found
        self.override       = override_default_prompt   # Overrides the default AI prompt used for building refined master_list bullet points
        self.force_models   = force_all_models          # This forces the sytem to download all models that the local device can effectively run 'well'.
                                                        # I.e., if your system can just run the 70b model, it will only force install 32b and below.
                                                        # NOTE: This takes up a lot of local storage. Make sure the space exists!

        self.save_dir       = save_directory            # Where to save everything

        # Interval variables
        self.R1models           = [ '671', '70', '32', '14', '8', '7', '1.5' ]
        self.R1modelsFlt        = [ 671, 70, 32, 14, 8, 7, 1.5 ]
        self.bullets_lists      = []
        self.mList              = {}                        # Dictionary of master list values 
        self.master_modeled     = ""                        # file of the DeepSeek edited master_file
        self.master_mod_found   = False                     # Whether the DeepSeek edited master_modeled file was found
        self.master_list        = {}                        # Dictionary of all experiences. This contains the values procesed from DeepSeek
        self.max_model_id       = 0


        ########## CONFIGURE DEEPSEEK MODEL
        # Check that the modelSize actually exists in the R1 models list
        if self.modelSize not in self.R1models:

            print( f"{self.modelSize}b not a recognized DeepSeek R1 model. Finding closest model size." )
            # Find the closest model size
            closest_model   = self.R1modelsFlt[0]
            min_difference  = 1000

            for number in self.R1modelsFlt:
                difference = abs(number - self.modelSizeFloat)
                if difference < min_difference:
                    min_difference  = difference
                    closest_model   = number
            
            self.modelSizeFloat = closest_model
            self.modelSize      = str( closest_model )

            print( f"Closest model chosen is deepseek-r1:{self.modelSize}b" )


        # Double check system capabilities
        max_modelNum  = self.get_max_model_size()

        # Convert max_model to string
        max_modelNum = round(max_modelNum,1)

        if max_modelNum>1.5:
            max_modelNum = int(max_modelNum)

        max_model = str(max_modelNum)

        self.max_model_id = self.R1models.index( max_model )

        # Just to make sure we're not bogging down our system
        if max_modelNum < self.modelSizeFloat:
            print( f"Reducing Model size to {max_model}b instead of {self.modelSize}b due to limited system capabilities" )
            self.modelSize = max_model

        # Download all lower level models
        if self.force_models:
            max_id          = self.R1models.index( max_model )+1

            # make new sliced list
            install_models  = self.R1models[max_id:]

            # Get models already installed
            curr_models     = ollama.list()

            inst_models     = [ a['model'] for a in curr_models.models ]

            # Cycle through all
            for md in install_models:

                mdl = f"deepseek-r1:{md}b"

                if not mdl in inst_models:
                    print( f"Model {mdl} not found!" )
                    print( f"Installing model {mdl}..." )
                    ollama.pull(mdl)


        ########## CONFIGURE PROMPT
        self.prompt  = "You are an expert at preparing resumes with over 20 years of experience. \
            Rewrite the following bullet points from a resume in a way that is both conducive to Applicant Tracking System filters and quantitive for \
            overcoming hiring manager requirements. Only give a response with the bullets in an unordered list with markdown language syntax. \
            Here are the bullet points to analyze:\n"
        if self.override:
            # Check to make sure `prompt` isn't blank
            if not prompt == '':
                self.prompt = prompt


        ########## CONFIGURE MASTER LIST BULLET POINTS   
        # Check if pre-configured master-lists already exist in master_file directory
        # format will be master_file_name_{self.modelSize}.json
        if self.master_list == "":
            base_name   = "masterlist_example"
        else:
            base_name           = os.path.basename( self.master_file )[:-5]
        mast_mod_fn         = base_name+"_"+self.modelSize+"b.json"
        self.master_modeled = os.path.join( self.save_dir, mast_mod_fn )

        # Check if file already exists
        if os.path.isfile( self.master_modeled ):
            print( f"{mast_mod_fn} already exists! Will use this file, unless forced overwrite set." )
            self.master_mod_found = True

        if self.force_rebuild:
            if os.path.exists(self.master_modeled):
                # Remove the file and start rebuild
                os.remove( self.master_modeled )
            self.master_mod_found = False

    # Processes all steps necessary for rebuilding the masterlist
    def process( self ):

        # Check if master_mod_found. If so, just load this and return.
        if self.master_mod_found:
            print( f"master_mod:\n({self.master_modeled})\nwas found! Using previously calculated results." )
            with open(self.master_modeled, 'r') as file:
                self.master_list = json.load( file )
        else:
            # Create the self.master_modeled file from DeepSeek by using self.mList derived from parse_masterlist()
            self.parse_masterlist()

            new_bullets = self.process_master_list()

            # Set the new masterlist
            self.master_list = self.mList

            for i, nb in enumerate( new_bullets ):
                bc  = len( self.master_list['experiences'][i]['projects'] )
                for j, n in enumerate( nb ):

                    # Only add the bullets we have space for. Sometimes the AI adds extra bullets.
                    if j < bc:
                        self.master_list['experiences'][i]['projects'][j]['description'] = n

            # Create new JSON file from saved master_list
            with open( self.master_modeled, 'w') as file:
                json.dump( self.master_list, file, indent = 4 )

    # Opens the masterlist.json and builds out new lists from given models
    def parse_masterlist( self ):

        self.bullets_lists = []

        # Check if masterlist exists
        if not os.path.isfile(self.master_file):
            raise FileNotFoundError( errno.ENOENT, os.strerror(errno.ENOENT), self.remastered_json )
        # Check that it is JSON format
        if not self.master_file.lower().strip().endswith( ".json" ):
            raise ValueError("Unsupported file type. Only .json files are allowed.")
        
        # Continue parsing
        with open(self.master_file, 'r') as file:
            self.mList = json.load(file)

        # Parse experiences into self.bullets_lists
        for v in self.mList['experiences']:
            self.bullets_lists.append( v['projects'] ) # Appends each experience list of bullets

    # DONE: Returns the system info of the current machine
    def get_system_info( self ):
        
        """Retrieves and prints system RAM, GPU presence, and GPU VRAM."""

        # Build return dict
        ret_dict    = {}

        # System RAM
        ram                     = psutil.virtual_memory()
        ret_dict['total_RAM']   = ram.total/( 1024**3 )  # Convert to GB
        ret_dict['avail_RAM']   = ram.available/( 1024**3 )

        # GPU Information
        ret_dict['gpu_exists']  = False
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                ret_dict['gpu_exists']  = True

                gpu_list    = []
                gpu_vram    = 0.
                for gpu in gpus:
                    gpu_list.append( { 'gpu_name': gpu.name, 'gpu_uuid': gpu.uuid } )
                    total_vram_mb = gpu.memoryTotal
                    gpu_vram += total_vram_mb/1024

                ret_dict['gpu_vram'] = gpu_vram
                ret_dict['gpu_list'] = gpu_list

            else:
                ret_dict['gpu_vram'] = 0.
                ret_dict['gpu_list'] = []

        except Exception as e:
            print( f"\nError getting GPU information: {e}" )
            print( "Make sure you have the 'gputil' library installed. (pip install gputil)" )

        return ret_dict
    
    # DONE: Determines the maximum model size that can run on the current machine
    def get_max_model_size( self ):

        """Checks max Deepseek model that can be used, based on tested systems from the internet
        
            Values taken from: https://dev.to/askyt/deepseek-r1-671b-complete-hardware-requirements-optimal-deployment-setup-2e48
        
        """

        # Set the model size v VRAM
        modelSizesRAM   = { '671':1342, '70':32.7, '32':14.9, '14':6.5, '8':3.7, '7':3.3, '1.5':0.7 }

        # Get the system values
        sys_vals        = self.get_system_info()

        print( f"Total CPU RAM: {sys_vals['total_RAM']}GB" )
        if sys_vals['gpu_exists']:
            print( f"GPU Found. GPU VRAM: {sys_vals['gpu_vram']}GB" )

        # Check system values against model sizes
        max_VRAM_model  = modelSizesRAM['1.5']
        max_RAM_model   = modelSizesRAM['1.5']

        for key, val in modelSizesRAM.items():

            # Consider if GPU exists for max_VRAM_model
            if sys_vals['gpu_exists']:
                if sys_vals['gpu_vram'] > val:
                    if float(key) > max_VRAM_model:
                        max_VRAM_model = float(key)

            # Consider the CPU side for max_RAM_model
            if sys_vals['total_RAM'] > val:
                if float(key) > max_RAM_model:
                    max_RAM_model = float(key)

        # Return the greater of the two
        return max_VRAM_model if max_VRAM_model>=max_RAM_model else max_RAM_model

    # DONE: Processes the bullets lists from the master_list with the given DeepSeek model
    def process_master_list( self ):
        
        new_bullet_lists    = []
        modelName           = f'deepseek-r1:{self.modelSize}b'

        # Get the length of the experiences
        exp_length = len( self.bullets_lists )

        print( f"Loading model {modelName}..." )
        print() # Adds another line
        for i, experience in enumerate( self.bullets_lists ):

            print( f"Processing experience {i+1}/{exp_length}...", end = "\r" )

            prompt = self.prompt
            for project in experience:
                prompt += f"- {project['description']}\n"

            # Clean prompt
            #prompt = " ".join(prompt.split())
            prompt = re.sub(r"[ \t]+", " ", prompt)

            
            # Build request
            try:
                response: ChatResponse = chat( model = modelName, messages = [
                    {
                        'role': 'user',
                        'content': prompt,
                    }
                ]) #, format = BulletList.model_json_schema())
                new_bullet_lists.append( self.processLLMResponse( response.message.content ) )
                #new_bullet_lists.append( BulletList.model_validate_json( response.message.content ) )
            except ResponseError as e:
                if e.status_code == 404:
                    print( f"Model {modelName} not installed. Downloading model. Please Re-run" )
                    pull(modelName)

        return new_bullet_lists

    # DONE: Parses the text returned from the LLM into a usable list
    def processLLMResponse( self, response:str ):

        # Remove <think> component
        resp        = response.split( '</think>' )
        response    = resp[1]
        
        # Split string into new list
        blist       = response.split('\n-')[1:]

        # Remove the "- " characters from each line
        new_list = []
        for string in blist:
            # Clean the string and append it
            new_list.append(re.sub(r"[ \t]+", " ", string[1:]))
        return new_list

    # Process all models up to the maximum model for the sytem
    def process_all_models( self ):
        
        # Build list of models from self.max_model_id and reverse order.
        process_models_list = self.R1models[self.max_model_id:][::-1]
        print( f"Processing all models capable of running on this machine:\n   - {process_models_list}" )
        for m in process_models_list:
            print( f"Starting model deepseek-r1:{m}b..." )
            self.modelSize = m
            list_dir            = os.path.dirname( self.master_file )
            base_name           = os.path.basename( self.master_file )[:-5]
            mast_mod_fn         = base_name+"_"+m+"b.json"
            self.master_modeled = os.path.join( list_dir, mast_mod_fn )
            self.process()
            print( f"model {m} JSON file saved!" )

    # DONE Build a summary for a job posting
    def buildSummary( self, job_title, job_company, job_description ):
        
        # Take the current summary I have, along with the job description, company, and title, to create a summary
        summary     = self.master_list['summary']

        modelName   = f'deepseek-r1:{self.modelSize}b'

        # Initialize the prompt
        prompt      = f"You are an expert at preparing resumes with over 20 years of experience. \
            A job with the title '{job_title}' for a company named '{job_company}' has been posted with the \
            job description of:\n \
            '{job_description}' \n"

        # Autogenerate a summary based off of the entire resume
        # NOTE: Keep in mind that this can max out the maximum input tokens and result in an error!
        if summary == "":

            print( "No summary found. Generating summary from resume..." )

            # Build list of all relevant items from the resume (education, experiences, projects, pubs, presentations, patents, awards)

            resume_summary  = ""

            # Cycle through education
            if len( self.master_list['education'] ) > 0:
                
                resume_summary += "Education:\n"

                for edu in self.master_list['education']:
                    resume_summary += f"- Degree: {edu['degree']}"
                    if not edu['minor'] == "":
                        resume_summary += f" - Minor: {edu['minor']}"
                    resume_summary += f", School: {edu['school']}"
                    if not edu['thesis'] == "":
                        resume_summary += f", Thesis: {edu['thesis']}"
                    resume_summary += "\n"

            # Cycle through experiences
            if len( self.master_list['experiences'] ) > 0:

                resume_summary += "Work Experience:\n"

                for exp in self.master_list['experiences']:

                    resume_summary += f"- Title: {exp['jobtitle']}, Company: {exp['company']}\n"

                    # Cycle through bullets
                    for bullet in exp['projects']:

                        resume_summary += f"    - {bullet['description']}\n"

            # Cycle through projects
            if len( self.master_list['projects'] ) > 0:

                resume_summary += "Projects:\n"

                for proj in self.master_list['projects']:

                    resume_summary += f"- Title: {proj['title']}, Description: {proj['description']}\n"

            # Cycle through publications
            if len( self.master_list['publications'] ) > 0:

                resume_summary += "Publications:\n"

                for pub in self.master_list['publications']:

                    resume_summary += f"- Title: {pub['title']}\n"

            # Cycle through presentations
            if len( self.master_list['presentations'] ) > 0:

                resume_summary += "Presentations:\n"

                for pres in self.master_list['presentations']:

                    resume_summary += f"- Title: {pres['title']}\n"

            # Cycle through patents
            if len( self.master_list['patents'] ) > 0:

                resume_summary += "Patents:\n"

                for pat in self.master_list['patents']:

                    resume_summary += f"- Title: {pat['title']}\n"


            # Cycle through awards
            if len( self.master_list['awards'] ) > 0:

                resume_summary += "Awards:\n"

                for award in self.master_list['awards']:

                    resume_summary += f"- Title: {award['award']}, Organization: {award['organization']}, Description: {award['description']}\n"


            prompt      += f"The qualifications and experience for the candidate for the job are written below:\n\
            '{resume_summary}'\n \
            Write a summary for the candidate in first person in a way that highlights why the candidate is uniquely qualified for the job. \
            Keep the summary to one paragraph that is four senctences long."

        else:
            prompt      += f"The resume of the candidate applying for the job has a summary of their qualifications written below:\n \
            '{summary}' \n \
            Rewrite the summary for the candidate in first person in a way that highlights why the candidate is uniquely qualified for the job. Keep the summary \
            to one paragraph that is four sentences long."

        # Process request
        response: ChatResponse = chat( model = modelName, messages = [
            {
                'role': 'user',
                'content': prompt,
            }
        ]) #, format = BulletList.model_json_schema())

        # Remove <think> component
        r           = response.message.content
        resp        = r.split( '</think>' )
        
        return resp[1]
    
    # Generates and saves a cover letter
    def buildCoverLetter( self, job_title, job_company, job_description, save_dir = os.path.dirname(os.path.abspath(__file__)) ):
        
        modelName   = f'deepseek-r1:{self.modelSize}b'

        # Initialize the prompt
        prompt      = f"You are an expert at preparing resumes with over 20 years of experience. \
            A job with the title '{job_title}' for a company named '{job_company}' has been posted with the \
            job description of:\n \
            '{job_description}' \n"

        # Autogenerate a summary based off of the entire resume for the cover letter to use
        # NOTE: Keep in mind that this can max out the maximum input tokens and result in an error!

        # Build list of all relevant items from the resume (education, experiences, projects, pubs, presentations, patents, awards)

        resume_summary  = ""

        # Cycle through education
        if len( self.master_list['education'] ) > 0:
            
            resume_summary += "Education:\n"

            for edu in self.master_list['education']:
                resume_summary += f"- Degree: {edu['degree']}"
                if not edu['minor'] == "":
                    resume_summary += f" - Minor: {edu['minor']}"
                resume_summary += f", School: {edu['school']}"
                if not edu['thesis'] == "":
                    resume_summary += f", Thesis: {edu['thesis']}"
                resume_summary += "\n"

        # Cycle through experiences
        if len( self.master_list['experiences'] ) > 0:

            resume_summary += "Work Experience:\n"

            for exp in self.master_list['experiences']:

                resume_summary += f"- Title: {exp['jobtitle']}, Company: {exp['company']}\n"

                # Cycle through bullets
                for bullet in exp['projects']:

                    resume_summary += f"    - {bullet['description']}\n"

        # Cycle through projects
        if len( self.master_list['projects'] ) > 0:

            resume_summary += "Projects:\n"

            for proj in self.master_list['projects']:

                resume_summary += f"- Title: {proj['title']}, Description: {proj['description']}\n"

        # Cycle through publications
        if len( self.master_list['publications'] ) > 0:

            resume_summary += "Publications:\n"

            for pub in self.master_list['publications']:

                resume_summary += f"- Title: {pub['title']}\n"

        # Cycle through presentations
        if len( self.master_list['presentations'] ) > 0:

            resume_summary += "Presentations:\n"

            for pres in self.master_list['presentations']:

                resume_summary += f"- Title: {pres['title']}\n"

        # Cycle through patents
        if len( self.master_list['patents'] ) > 0:

            resume_summary += "Patents:\n"

            for pat in self.master_list['patents']:

                resume_summary += f"- Title: {pat['title']}\n"


        # Cycle through awards
        if len( self.master_list['awards'] ) > 0:

            resume_summary += "Awards:\n"

            for award in self.master_list['awards']:

                resume_summary += f"- Title: {award['award']}, Organization: {award['organization']}, Description: {award['description']}\n"


        prompt      += f"The qualifications and experience for the candidate named '{self.master_list['about']['name']}' for the job are written below:\n\
        '{resume_summary}'\n \
        Write a cover letter for the candidate in first person in a way that highlights why the candidate is uniquely qualified for the job. \
        Keep the cover letter to one page long."

        # Process request
        response: ChatResponse = chat( model = modelName, messages = [
            {
                'role': 'user',
                'content': prompt,
            }
        ]) #, format = BulletList.model_json_schema())

        # Remove <think> component
        r       = response.message.content
        resp    = r.split( '</think>' )

        # check for \u2082
        new_rsp = resp[1].replace( "\u2082", "<sub>2</sub>" )

        # Create a format for the cover letter in HTML
        now     = datetime.now()
        month   = now.strftime( "%B" )
        ret     = "<!DOCTYPE html><html><head><title>Resume</title></head><body>"
        ret     += f"<div class='cl_header'><div class='cl_date'>{now.day} {month}, {now.year}</div>"
        ret     += f"<div class='cl_company'>{job_company}</div>"
        ret     += "</div>"
        ret     += f"<div class='cl_letter'>{new_rsp}</div>"
        ret     += f"<div class='cl_signature'><div>Sincerely,</div><div>{self.master_list['about']['name']}</div></div>"
        ret     += "</body></html>"

        # Save the document and return it, just in case
        lastname            = self.master_list['about']['name'].split()[-1]
        jobTitle            = "".join(job_title.split())
        comp_name           = job_company.split()[0]
        basename            = f"{lastname}_{jobTitle.lower()}_{comp_name.lower()}"
        basename            += "_coverletter.html"

        save_file_loc       = os.path.join( save_dir, basename )

        with open( save_file_loc, "w" ) as file:
            file.write( ret )
        
        return ret, save_file_loc


if __name__ == "__main__":

    # Test the system
    ml_file = os.path.join( os.path.dirname(os.path.abspath(__file__)), "masterlist_example_small.json" )
    BR = BulletRebuilder( master_file = ml_file, modelSize = '1.5', force_rebuild = True )
    BR.process()
    #BR.process_all_models()


