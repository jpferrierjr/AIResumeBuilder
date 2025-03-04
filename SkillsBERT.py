'''

    Title:          BERT Top Skills

    Description:    This class compares given skills lists to a job description and returns skils that most match
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

# DONE: BERT bullet class
class BERTSkills:

    def __init__( self, 
                 skills:list            = [], 
                 subskills:list         = [],
                 job_title:str          = "", 
                 job_description:str    = "", 
                 BERTModel:str          = "all-mpnet-base-v2",
                 count:int              = 5 ):
        
        self.skillsList     = skills
        self.subskillslist  = subskills
        self.job_desc       = job_description
        self.count          = count
        self.job_title      = job_title
        self.BERTModel      = BERTModel

        self.results        = []
        self.fulldesc       = self.job_title + " " + self.job_desc

        # Concantenate the skills
        self.totalSkillslst = skills + subskills

    def render( self ):

        # Ensure that there are more skills that the listed count max
        if len( self.totalSkillslst ) > self.count:
            self.model      = SentenceTransformer( self.BERTModel )
            desc_embed      = self.model.encode( self.fulldesc )

            BERTRatings = []
            for b in self.totalSkillslst:
                b_embed     = self.model.encode( b['skill'] )
                BERTRatings.append( util.cos_sim( desc_embed, b_embed ).item() )

            # Combine the BERT ratings and the skills list for sorting
            comb_bs     = list( zip( BERTRatings, self.totalSkillslst ) )
            comb_bs     = sorted( comb_bs, key = lambda x: x[0], reverse = True )

            # Separate the lists
            _, sorted_skills    = zip( *comb_bs )

            # Create sorted list of skills
            s_skill_lst         = list( sorted_skills )

            # Set the results
            self.results        = s_skill_lst[:self.count]

        else:
            self.results = self.totalSkillslst

        return self.results


if __name__ == "__main__":

    # List of skills to evaluate
    skills      =[
        { 
            "id": 1,
            "skill": "Python", 
            "subskills": [ 1, 2, 3, 4, 5, 6, 7, 8, 9, 66, 72 ]
        },
        { 
            "id": 2,
            "skill": "Mechanical Engineering", 
            "subskills": [ 10, 11, 12, 13, 14, 15, 16 ]
        },
        { 
            "id": 3,
            "skill": "Computational Physics", 
            "subskills": [ 17, 18, 19, 20 ]
        },
        { 
            "id": 4,
            "skill": "Machine Learning",
            "subskills": [ 21, 22, 23, 24, 25, 26, 27 ]
        },
        { 
            "id": 5,
            "skill": "Condensed Matter Physics", 
            "subskills": [ 28, 29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41 ]
        },
        { 
            "id": 6,
            "skill": "Web Development", 
            "subskills": [ 42, 43, 44, 45, 46, 47, 48, 49, 50, 76 ]
        },
        { 
            "id": 7,
            "skill": "Software Engineering", 
            "subskills": [ 51, 52, 53, 54, 55 ]
        },
        { 
            "id": 8,
            "skill": "Electrical Engineering", 
            "subskills": [ 56, 57, 58, 71, 80 ]
        },
        { 
            "id": 9,
            "skill": "Computer Design", 
            "subskills": [ 59, 60, 61, 62, 63, 64, 65 ]
        }
    ]

    subskills = [
        { 
            "id": 1, 
            "skill": "Numpy"
        },
        { 
            "id": 2, 
            "skill": "Pandas"
        },
        { 
            "id": 3, 
            "skill": "SciPy"
        },
        { 
            "id": 4, 
            "skill": "ASE"
        },
        { 
            "id": 5, 
            "skill": "GPAW"
        },
        { 
            "id": 6, 
            "skill": "SciKit-Learn"
        },
        { 
            "id": 7, 
            "skill": "Tensorflow"
        },
        { 
            "id": 8, 
            "skill": "PyTorch"
        },
        { 
            "id": 9, 
            "skill": "PyQt"
        },
        { 
            "id": 10, 
            "skill": "SolidWorks"
        },
        { 
            "id": 11, 
            "skill": "FreeCAD"
        },
        { 
            "id": 12, 
            "skill": "AutoDesk"
        },
        { 
            "id": 13, 
            "skill": "CNC"
        },
        { 
            "id": 14, 
            "skill": "3D Printing"
        },
        { 
            "id": 15, 
            "skill": "Laser Cutting"
        },
        { 
            "id": 16, 
            "skill": "Microfluidics"
        },
        { 
            "id": 17, 
            "skill": "Quantum Chemistry"
        },
        { 
            "id": 18, 
            "skill": "Molecular Dynamics"
        },
        { 
            "id": 19, 
            "skill": "Fluid Dynamics"
        },
        { 
            "id": 20, 
            "skill": "Acoustics"
        },
        { 
            "id": 21, 
            "skill": "Bayesian Optimization"
        },
        { 
            "id": 22, 
            "skill": "Gaussian Processes"
        }
    ]
    
    # Job title to be considered (really just added for extra comparison)
    job_title   = "Experimental Physicist"
    
    # Job description to evaluate against
    job_desc    = """We have an opening for an Experimental Physicist to study high-energy-density and warm-dense-matter physics in laser-driven experiments. The role involves planning, designing, executing, and leading experiments on the National Ignition Facility (NIF), as well as other high power laser facilities, to support understanding of the physics governing laser-plasma interactions, hydrodynamics, radiation transport, implosion physics, material strength and nuclear physics. This position resides in High Energy Density (HED) Scientific & Technology (S&T) Program within the National Ignition Facility and Photon Science (NIF & PS) Principal Associate Directorate (PAD).

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

    # How many top skills to return
    count       = 5

    BS  = BERTSkills( skills = skills, subskills = subskills, job_title = job_title, job_description = job_desc, count = count )
    BS.render()

    print( BS.results )