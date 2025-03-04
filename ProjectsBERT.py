'''

    Title:          BERT Projects

    Description:    This class compares given projects dictionary to a job description and returns projects that most match
                    the job description in order of BERT score

    Author:         Dr. John Ferrier

    Date:           27 February 2025

'''

# Import libraries
import os
import json
import string
from typing import Optional
from sentence_transformers import SentenceTransformer, util


class BERTProjects:

    def __init__( self,
                job_title:str       = "", 
                job_description:str = "", 
                projects:list       = [],
                BERTModel:str       = "all-mpnet-base-v2",
                count:int           = 5  ):
        
        self.job_desc   = job_description
        self.projects   = projects
        self.count      = count
        self.job_title  = job_title
        self.BERTModel  = BERTModel

        self.results    = {}
        self.fulldesc   = self.job_title + " " + self.job_desc

    # Process the BERT model
    def render( self ):
        # Ensure that there are more projects that the listed count max
        if len( self.projects ) > self.count:
            self.model      = SentenceTransformer( self.BERTModel )
            desc_embed      = self.model.encode( self.fulldesc )

            BERTRatings = []
            for b in self.projects:
                b_embed     = self.model.encode( f"{b['title']} - {b['description']}" )
                BERTRatings.append( util.cos_sim( desc_embed, b_embed ).item() )

            # Combine the BERT ratings and the skills list for sorting
            comb_bs     = list( zip( BERTRatings, self.projects ) )
            comb_bs.sort( reverse = True )

            # Separate the lists
            _, sorted_projects  = zip( *comb_bs )

            # Create sorted list of projects [list of dictionaries]
            s_projects_lst      = list( sorted_projects )

            # Set the results
            self.results        = s_projects_lst[:self.count]

        else:
            self.results = self.projects

        return self.results
    
    

if __name__ == "__main__":

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

    projects = [
        {
            "id": 1,
            "title": "Raman Spectroscope Rebuild",
            "link": "https://github.com/jpferrierjr/",
            "description": "Disassembled an old broken Renishaw Raman spectroscope and rebuilt it from the ground up. A new circuit board was designed for handling the motors for smoother and faster data collection. A new CCD was installed and dynamically controlled from the custom operating software designed with Python and Qt Designer. The new system had autocalibration and live feeds from both the microscope and the CCD. The software also implemented an automated peak finder and peak fitting functions, along with other analysis functions.",
            "skillsUsed": [ 1, 2, 7, 8, 9 ],
            "subSkillsUsed": [ 1, 2, 3, 9, 10, 14, 33, 45, 52, 56, 57, 58, 61, 65 ]
        },
        {
            "id": 2,
            "title": "Sentiment Analysis Stock Trader",
            "link":"",
            "description": "Designed a stock analyzing software that would utilize a sentiment analysis machine learning model to read stock news before the market opens to determine whether to trade stocks. The system was originally designed to integrate into the Robinhood trading software and handle daily trading activities by checking all stock values every 1 second. The software was designed to store and track each purchase, sell, and 1-second change of all stocks owned. Multiple model parameters were used for determining the limits for which to sell a stock at, resulting in some models averaging a ~200% annual return. Lower models averaged ~60% annual return.",
            "skillsUsed": [ 1, 4, 7 ],
            "subSkillsUsed": [1, 8, 24, 25, 27, 52, 55]
        },
        {
            "id": 3,
            "title": "Chemical Vapor Deposition Flow Rate Controller",
            "link": "",
            "description": "Developed a system for dynamically controlling up to 3 CVD flow controllers. The system provided power to the flow constrollers, tracked the flow rates in real-time, and auto-adjusted flow rates to match desired settings. The system was also designed to allow for more complex changes and timings to flow rates, such as mathematical function derived flow rate curves. The system also tracked pressure alarms for the CVD system to allow for an automated emergency shutoff of all gas flow.",
            "skillsUsed": [ 2, 5, 7, 8 ],
            "subSkillsUsed": [ 10, 14, 29, 31, 51, 56, 57, 58, 71 ]
        },
        {
            "id": 4,
            "title": "Lattice Boltzmann Fluid Dynamics Simulator",
            "link": "",
            "description": "",
            "skillsUsed": [ 1, 3, 7 ],
            "subSkillsUsed": [ 1, 52, 83 ]
        },
        { 
            "id": 5,
            "title": "Electron Cloud Density Visualizer - Blender3D Plugin",
            "description": "",
            "link": "",
            "skillsUsed": [ 1, 3, 5, 7 ],
            "subSkillsUsed": [ 1, 4, 5, 17, 18, 28, 38, 52, 66, 82 ]
        }
    ]

    BP = BERTProjects(  job_title       = jobTitle,
                        job_description = jobdesc,
                        projects        = projects,
                        count           = 2 )
    
    BP.render()

    print( BP.results )