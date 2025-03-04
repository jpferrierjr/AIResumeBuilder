'''

    Title:          BERT Comparator

    Description:    This class compares given bullet lists to a job description and returns bullet points that most match
                    the job description in order of BERT score

    Author:         Dr. John Ferrier

    Date:           8 February 2025

'''

# Import libraries
import os
import json
import string
from typing import Optional
from sentence_transformers import SentenceTransformer, util

# DONE: BERT bullet class
class BERTBullets:

    # DONE: Initialize the class
    def __init__(
        self,
        jobTitle:str            = "",                                           # Job Title that you're applying to
        jobCompany:str          = "",                                           # Company name that you're applying to
        jobDesc:str             = "",                                           # Given job description that you're applying to
        bulletPoints:list[dict] = [],                                           # List of each bullet point under each experience [ { type:1, bullets:[], title:"" }, {} ]
        minPoints:Optional[int] = 3,                                            # Minimum amount of bullets per experience. If 0, experience removed if low BERT score
        BERTModel:str           = "all-mpnet-base-v2",                          # The BERT model to use.
        save_location:str       = os.path.dirname(os.path.abspath(__file__)),   # The save location for the processed data
        force_rebuild:bool      = False,                                         # Whether to force a rebuile of the saved files. This is mostly done for testing.
        save_files:bool         = True
    ):
    
        # Externally set variables
        self.jobTitle           = jobTitle
        self.jobCompany         = jobCompany
        self.jobDesc            = jobDesc
        self.bulletPnts         = bulletPoints
        self.minPnts            = minPoints
        self.BERTmodel          = BERTModel
        self.force_rebuild      = force_rebuild
        self.save_location      = save_location
        self.save_files         = save_files

        # Internal
        self.newBulletPnts      = []

        # Check that the save location exists
        if not os.path.exists( self.save_location ):
            # Create it
            os.mkdir( self.save_location )

        # This should be of the form company_title_bulletpoints{5}_bertmodel.json
        results_file_name       = f"{self.prepare_text_for_filename(self.jobCompany)}_{self.prepare_text_for_filename(self.jobTitle)}_bpcount{len(self.bulletPnts)}_BERTModel-{self.BERTmodel}"
        self.BERTResultsFile    = os.path.join( save_location, f"{results_file_name}.json" )

        # Only use this for testing purposes
        if self.force_rebuild:
            # Remove the BERTResultsFile if it exists
            if os.path.isfile( self.BERTResultsFile ):
                os.remove( self.BERTResultsFile )
    
    # DONE: Renders the result of BERT testing
    def render( self ):

        # First, check if the file already exists. If so, skip the rest.
        if os.path.isfile( self.BERTResultsFile ):

            print( "Found previous BERT Results File!" )
            # Open the file and save the results to self.newBulletPnts
            with open(self.BERTResultsFile, 'r') as file:
                self.newBulletPnts = json.load(file)
        else:
            print( f"{self.BERTResultsFile} not found! Starting model" )
            print( f"Loading BERT model {self.BERTmodel}..." )
            # Load the model
            self.model      = SentenceTransformer( self.BERTmodel )

            print( "Encoding Job Description for BERT model..." )
            # Encode the job description
            desc_embed      = self.model.encode( self.jobDesc )

            # Define the new bulletPoints variable
            newBulletPnts   = []

            print( "Staring BERT Processing Cycle..." )
            # Cycle through the bullet points for each experience
            # self.bulletPnts = structure( { 'type':1, 'title':v['jobtitle'], 'bullets':v['projects'] } )
            for exp in self.bulletPnts:

                # Get the count of bullet points
                bPntCnt     = len( exp['bullets'] )

                # Build the bullet count limit
                bCntLimit   = bPntCnt

                # Limit the points to the set cap, if defined
                if self.minPnts > 0:
                    if self.minPnts < bCntLimit:
                        bCntLimit = self.minPnts

                # Cycle through each bullet point for BERT ratings
                BERTRatings = []
                for b in exp['bullets']:
                    b_embed     = self.model.encode( b['description'] )
                    BERTRatings.append( util.cos_sim( desc_embed, b_embed ).item() )

                # Combine the BERT ratings and the bullets list for sorting
                comb_bs     = list( zip( BERTRatings, exp['bullets'] ) )
                comb_bs     = sorted( comb_bs, key = lambda x: x[0], reverse = True )

                # Separate the lists
                sorted_BERT, sorted_bullets = zip( *comb_bs )

                # Create the new dictionary
                newD            = {}
                newD['type']    = exp['type']
                newD['title']   = exp['title']

                # Create sorted lists
                s_BERT_lst      = list( sorted_BERT )
                s_bull_lst      = list( sorted_bullets )

                # Limit the bullets by count limit
                newD['bullets'] = s_bull_lst[:bCntLimit]
                newD['BERTS']   = s_BERT_lst[:bCntLimit]

                # Append the new points
                newBulletPnts.append( newD )

            # Set new bullets list to a global variable (just in case for extra usage)
            self.newBulletPnts = newBulletPnts

            # Save the results for future use
            if self.save_files:
                self.save_results()

        # Return the values
        return self.newBulletPnts
    
    # DONE: Processes input text to remove punctuation/spaces. Puts all text to lowercase
    def prepare_text_for_filename( self, text:str = "" ):

        # Remove punctuation
        text = text.translate( str.maketrans('', '', string.punctuation ) )

        # Remove spaces and convert to lowercase
        words = text.lower().split()

        # Camelcase the words
        camelcase_text = words[0] if words else ""
        for word in words[1:]:
            camelcase_text += word.capitalize()

        return camelcase_text
        
    # DONE: Saves the BERT files for each job.
    def save_results( self ):
        print( f"Saving BERT model results to {self.BERTResultsFile}" )
        with open( self.BERTResultsFile, 'w') as file:
            json.dump( self.newBulletPnts, file, indent = 4 )
    
# Local testing
if __name__ == "__main__":

    jobComp     = "ACME inc."
    jobTitle    = "Experimental Physicist"

    jobdesc     = """We have an opening for an Experimental Physicist to study high-energy-density and warm-dense-matter physics in laser-driven experiments. The role involves planning, designing, executing, and leading experiments on the National Ignition Facility (NIF), as well as other high power laser facilities, to support understanding of the physics governing laser-plasma interactions, hydrodynamics, radiation transport, implosion physics, material strength and nuclear physics. This position resides in High Energy Density (HED) Scientific & Technology (S&T) Program within the National Ignition Facility and Photon Science (NIF & PS) Principal Associate Directorate (PAD).

    You will

    Contribute as a member of an interdisciplinary team to design and execute X-ray and laser driven experiments studying warm-dense matter and high-energy density physics at the NIF, OMEGA, and other facilities.
    Design, field, and coordinate optical, X-ray and nuclear diagnostics.
    Document and publish research results for internal audiences and in peer-reviewed scientific or technical journals, present results at conferences, workshops, and seminars, and write periodic progress reports that capture and communicate research results.
    Collaborate with scientists and researchers and other stakeholders to accomplish research goals and organizational objectives.
    Coordinate team resources and plan experimental projects/campaigns.
    Engage with complementary research efforts and interact with broad spectrum of scientists internal and external to the Laboratory.
    Perform other duties as assigned.

    Qualifications

    The 2025 National Defense Authorization Act (NDAA), Section 3112, generally prohibits citizens of China, Russia, Iran and North Korea without dual US citizenship or legal permanent residence from accessing specific non-public areas of national security or nuclear weapons facilities. The restrictions of NDAA Section 3112 apply to this position. To be qualified for this position, candidates must be eligible to access the Laboratory in compliance with Section 3112.
    Ability to secure and maintain a U.S. DOE Q-level security clearance which requires U.S. citizenship.
    PhD in plasma physics, hydrodynamics, shock physics, spectroscopy, condensed matter, nuclear physics, dynamic material science, or related discipline.
    Advanced experience and knowledge in independent design, executing, and analyzing complex experiments at high-power laser facilities, in one of the following areas: laser-plasma interactions, hydrodynamics, radiation driven hydrodynamics, radiation transport, nuclear physics or high energy density experiments.
    Advanced experience developing, calibrating and fielding x-ray, optical or nuclear diagnostics and associated analysis techniques.
    Advanced verbal and written communication skills necessary to work in a multidisciplinary team environment, author technical and scientific reports and publications and deliver scientific presentations.
    Experience working independently with minimal direction and effective interpersonal skills necessary to collaborate and work in a team environment.

    Qualifications We Desire

    Experience with developing and implementing nuclear and x-ray diagnostics to study materials at extreme temperatures and pressures in NIF and Omega experiments.
    Experience with data analysis tools and algorithms in Python, Matlab, or similar language.
    Experience with 1D and 2D radiation hydrodynamic codes."""

    # Types: 1 = Work exp, 2 = projects
    bPnts   = [ 
        { 
            'type':1, 
            'bullets':
            [
                { 
                    "id":1, 
                    "description": "Created new thermodynamic methods for predicting 2D quantum material synthesis", 
                    "skills":[ 1, 3, 5, 7 ], 
                    "subskills":[ 1, 2, 3, 4, 5, 17, 18, 28, 29, 31, 38, 39, 41, 52, 55, 59, 60, 61, 62, 63 ]
                },
                { 
                    "id":2, 
                    "description": "Analyzed the effectiveness of differing machine learning models for predicting 2D quantum material synthesis experimental parameters (Bayesian Optimization with Gaussian Processes vs Deep Neural Networks)", 
                    "skills":[ 1, 4, 5, 7 ], 
                    "subskills":[ 1, 2, 3, 6, 7, 17, 21, 22, 23, 29, 31, 33, 41, 52, 55, 59, 60, 61, 63 ] },
                { 
                    "id":3, 
                    "description": "Discovered a new method for synthesizing graphene at lower temperatures, higher pressures, and lower cost than traditional methane-based methods",
                    "skills":[1,3,5,12], 
                    "subskills":[1,4,5,17,18,28,29,31,33,35,36,37,38,39,41,52,59,62,63] 
                },
                { 
                    "id":4, 
                    "description": "Designed and built a fully-functional and self-calibrating Raman Spectroscope with a full GUI-based user software, new circuit design, and higher speed motor control testing for faster Raman measurements",
                    "skills":[1,2,4,7,8,9], 
                    "subskills":[1,3,9,10,14,15,28,33,52,56,57,58,61,65,71,72]
                },
                { 
                    "id":5, 
                    "description": "Built custom circuit boards for full digital controls over Chemical Vapor Deposition (CVD) gas flow controllers for more precise experimental control.",
                    "skills":[1,2,7,8],
                    "subskills":[1,9,10,14,51,52,56,57,58,65]
                },
                {
                    "id":6,
                    "description": "Developed Computational Fluid Dynamics software for predicting CVD gas flow using the Lattice Boltzmann method", 
                    "skills":[1,3,7],
                    "subskills":[1,3,19,31]
                },
                {
                    "id":7,
                    "description": "Performed fundamental theoretical and experimental experiments to discover the synthesis parameters of K<sub>2</sub>CoS<sub>2</sub>",
                    "skills":[1,3,5,7,12],
                    "subskills":[1,3,4,5,17,18,28,29,30,31,32,33,34,38,39,40,41,52,59,62,63]
                },
                {
                    "id":8,
                    "description": "Worked with NASA engineers to devise a method for synthesizing graphene aboard the ISS in order to research the role of convection on synthesis",
                    "skills":[2,5],
                    "subskills":[10,13,19,29,31,73,77,83]
                },
                {
                    "id":9,
                    "description": "Designed a robotic system for automated 2D material stacking",
                    "skills":[2,5],
                    "subskills":[10]
                },
                {
                    "id":11,
                    "description": "Developed a Blender plugin tool to visualize DFT electron cloud densities in Blender3D",
                    "skills":[1,3,7],
                    "subskills":[1,4,5,17,28,38,52,66,82]
                },
                {
                    "id":12,
                    "description": "Created an automated Raman fitting and analysis software to allow researchers to perform high-throughput data collection",
                    "skills":[1,7],
                    "subskills":[1,3,9,33,86]
                },
                {
                    "id":13,
                    "description": "Developed an automated mapped Raman fitting and analysis software [for a different Raman system than the one above]",
                    "skills":[1,7],
                    "subskills":[1,3,9,33,72,86]
                },
                {
                    "id":14, 
                    "description": "Built a comprehensive automated DFT software that categorizes materials, converges DFT values, and saves pre-calculated values to reduce future computation",
                    "skills":[1,3,5,7,12],
                    "subskills":[1,3,4,5,17,18,28,29,38,39,59,60,61,62,63,77]
                },
                {
                    "id":15,
                    "description": "Worked with the NEU Physics department to develop an interactive Muon detector project for use with science outreach programs. This was an updated and more interactive version of the MIT CosmicWatch",
                    "skills":[2,7,8],
                    "subskills":[10,51,56,57,58,65,71]
                },
                {
                    "id":16,
                    "description": "Before the addition of GPAW to conda-forge, developed a shell script to allow for the install of GPAW onto ARM-based Mac products.",
                    "skills":[1,3,5,7], 
                    "subskills":[17,38,52,55,60,87]
                },
                {
                    "id":17, 
                    "description": "Trained both undergraduate and graduate students on experimental condensed matter physics protocols and SOPs",
                    "skills":[11], 
                    "subskills":[73,74,78,84]
                },
                {
                    "id":18, 
                    "description": "Managed laboratory safety trainings, purchasing, chemical inventories, and safety compliance.",
                    "skills":[11],
                    "subskills":[73,75,84]
                }
            ], 
            'title':'Northeastern University'
        },
        { 
            'type':1, 
            'bullets':
            [
                {
                    "id":1,
                    "description": "Ensured proper safety protocols were followed by researchers.",
                    "skills":[11],
                    "subskills":[73]
                }, 
                {
                    "id":2,
                    "description": "Managed grant purchasing for lab supplies for researchers.",
                    "skills":[11], 
                    "subskills":[75]
                }, 
                { 
                    "id":3, 
                    "description": "Trained and assisted researchers on lab equipment usage and maintenance.",
                    "skills":[11], "subskills":[78]
                },
                {
                    "id":4, 
                    "description": "Compiled and managed year-end meetings.", 
                    "skills":[11], 
                    "subskills":[84]
                },
                { 
                    "id":5, 
                    "description": "Served as Lab Safety lead, working with EH&S on inspections and compliance.", 
                    "skills":[11], 
                    "subskills":[73]
                },
                { 
                    "id":6, 
                    "description": "Performed annual inventories and managed lab routine clean-up activities.", 
                    "skills":[11], 
                    "subskills":[73,84]
                },
                { 
                    "id":7, 
                    "description": "Managed and guided lab preparations for tours of distinguished guests.",
                    "skills":[11],
                    "subskills":[84]
                },
                { 
                    "id":8, 
                    "description": "Oversaw 40+ lab members and served as an intermediary for lab culture and conflict resolution.",
                    "skills":[11],
                    "subskills":[73,74]
                }
            ], 'title':'Harvard University School of Engineering and Applied Sciences'
        }
    ]

    BB = BERTBullets( jobCompany = jobComp, jobTitle = jobTitle, jobDesc = jobdesc, bulletPoints = bPnts )

    BB.render()

    print( BB.newBulletPnts )