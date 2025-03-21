// job_offer_extractor.baml - BAML file for extracting structured job offer information from webpage text

// Structured output class for Job Offers
class JobOfferStructure {
  company_name string? @description("Name of the company offering the job")
  job_title string @description("Title of the job position") @assert(valid_length, {{ this|length > 0 }})
  location string? @description("Location of the job (city, region, country)")
  job_type string? @description("Type of job: full-time, part-time, contract, internship, etc.")
  company_description string? @description("Brief description of the company")
  job_description string? @description("Description of the job position")

  responsibilities string @description("Responsibilities and tasks for the position")
  requirements string @description("Required qualifications, skills, and experience")

  benefits string? @description("Benefits and perks offered with the position")

  salary_range string? @description("Salary range or compensation information if available")
  application_deadline string? @description("Application deadline if specified")

  contact_info string? @description("Contact information for applications")
  application_instructions string? @description("Instructions on how to apply")


  additional_info string? @description("Any additional relevant information about the position")

  @@assert(has_essential_info, {{
    this.job_title is not none and
    this.responsibilities|length > 0 and
    this.requirements|length > 0
  }})
}

// Function for extracting job offer information from webpage text
function ExtractJobOffer(
  webpage_text: string @assert(not_empty, {{ this|length > 0 }})
) -> JobOfferStructure {
  client LLMFallback
  prompt #"# Job Offer Information Extraction

## Objective
Extract structured information about a job offer from the provided webpage text. The extracted information will be used to generate personalized cover letters.

## Critical Rules
1. Extract ONLY factual information present in the text - never invent or assume details
2. If information for a field is not available, leave it empty/null
3. Preserve the original language of the job offer (French, English, German, etc.)
4. Focus on extracting information relevant for a job application
5. Ensure the extracted information is well-structured for later use by an LLM

## Extraction Guidelines

### Company Information
- Extract the exact company name as mentioned
- Include a brief description of the company if available
- Do not invent company details if not explicitly stated

### Job Details
- Extract the complete and exact job title
- Identify the location (city/region/country)
- Determine job type (full-time, part-time, contract, etc.)
- Extract salary information if available

### Key Content Areas
- Responsibilities: Extract all mentioned job duties and responsibilities as separate list items
- Requirements: Extract all qualifications, skills, and experience requirements as separate list items
- Benefits: Extract all mentioned benefits and perks as separate list items

### Application Information
- Extract application deadline if specified
- Include contact information for applications
- Note any specific application instructions

## Processing Instructions
1. Analyze the entire text to identify relevant sections
2. Extract information according to the output schema
3. Maintain the original language and terminology
4. Preserve important details that would be relevant for a cover letter
5. Format lists as clear, separate items
6. Ensure all extracted information is accurate and present in the source text

## Webpage Text:
{{ webpage_text }}

{# special macro to print the output schema instructions #}
{{ ctx.output_format }}
"#
}

// Tests for the function
test BasicJobOfferExtractionTest {
  functions [ExtractJobOffer]
  args {
    webpage_text #"Ingénieur en Automatisation - Yverdon-les-Bains

Tech Solutions SA, leader dans le domaine de l'automatisation industrielle, recherche un ingénieur qualifié.

Missions :
- Développement de solutions d'automatisation
- Optimisation des processus industriels
- Support technique aux clients

Profil requis :
- Diplôme d'ingénieur en automatisation
- Expérience en programmation PLC
- Français et anglais courant

Avantages :
- Salaire attractif
- Horaires flexibles
- Équipement moderne

Postulez en ligne sur notre plateforme de recrutement."#
  }
}

test DetailedJobOfferExtractionTest {
  functions [ExtractJobOffer]
  args {
    webpage_text #"Vous êtes ingénieur.e de projet en électricité ? Vous possédez une expérience en Suisse ? Alors n'hésitez plus et postulez !

Cette entreprise internationale est reconnue pour son expertise technologique avancée, offrant des solutions sur mesure dans divers secteurs industriels. Actuellement, elle recherche un-e Ingénieur-e de projet électricien-ne pour concevoir, mettre en oeuvre et gérer des systèmes électriques, tout en assurant le respect des normes de sécurité et des spécifications clients.

Vos activités chez votre futur employeur :

Vous collaborez avec des ingénieur-e-s et des technicien-ne-s pour concevoir et améliorer des systèmes électriques
Vous analysez des machines existantes afin d'optimiser leurs performances et de proposer des améliorations
Vous développez des processus de fabrication conformes aux normes internationales en vigueur
Vous dirigez des projets d'ingénierie, en veillant au respect des délais et à l'atteinte des objectifs fixés
Vous définissez les besoins des clients et proposez des solutions adaptées à leurs exigences spécifiques

Vos atouts pour votre futur employeur :

Vous êtes titulaire d'un diplôme en ingénierie électrique
Vous possédez une expérience en gestion de projets et en coordination d'équipes
Vous avez la capacité de diagnostiquer des équipements et d'effectuer des tests complexes sur des systèmes
Vous maîtrisez le français et l'anglais, avec d'excellentes compétences en communication
Vous êtes à jour sur les technologies émergentes et engagé-e dans un processus d'apprentissage continu

Vous pourrez bénéficier de avantages suivants :

Vous profitez d'horaires de travail flexibles, favorisant un équilibre entre vie professionnelle et personnelle
Vous évoluez dans un environnement qui valorise l'équité, la diversité et l'inclusion, créant un cadre de travail respectueux et collaboratif
Vous bénéficiez d'un soutien actif pour votre développement professionnel, avec des opportunités de formation continue et de progression de carrière
Vous participez à des projets innovants, contribuant à des solutions de pointe dans le secteur des matériaux avancés

Nous avons éveillé votre intérêt ? Alors postulez dès aujourd'hui !

Lieu du travail: Yverdon-les-Bains.
Contact: Laura Rudaz-Truscello, Écrire un email, +41 21 613 06 60 ID: 666529"#
  }
}

test EnglishJobOfferExtractionTest {
  functions [ExtractJobOffer]
  args {
    webpage_text #"Software Engineer - Remote

About Us:
TechCorp is a leading software development company specializing in cloud solutions and AI applications. We are currently looking for a talented Software Engineer to join our growing team.

Job Description:
We are seeking a Software Engineer with strong programming skills and a passion for creating efficient, scalable applications. The ideal candidate will work collaboratively with our development team to design, code, and maintain software solutions.

Responsibilities:
• Design and develop high-quality software solutions
• Collaborate with cross-functional teams to define and implement new features
• Write clean, maintainable code with appropriate documentation
• Perform code reviews and ensure code quality
• Troubleshoot, debug and upgrade existing systems
• Stay up-to-date with emerging trends and technologies

Requirements:
• Bachelor's degree in Computer Science or related field
• 3+ years of experience in software development
• Proficiency in at least one programming language (Python, Java, C#)
• Experience with web development frameworks
• Knowledge of database systems and cloud services
• Strong problem-solving abilities and attention to detail
• Excellent communication and teamwork skills

Benefits:
• Competitive salary: $80,000 - $120,000 based on experience
• Remote work flexibility
• Health insurance and retirement plans
• Professional development opportunities
• Paid time off and holidays
• Modern equipment and software licenses

Application Process:
Please submit your resume and a cover letter explaining why you're interested in this position to careers@techcorp.com by June 30, 2023.

TechCorp is an equal opportunity employer and values diversity in the workplace."#
  }
}

test GermanJobOfferExtractionTest {
  functions [ExtractJobOffer]
  args {
    webpage_text #"Stellenangebot: Elektroingenieur/in

Unser Unternehmen sucht einen erfahrenen Elektroingenieur für unseren Standort in Zürich.

Ihre Aufgaben:
- Entwicklung elektrischer Systeme
- Projektleitung und Teamkoordination
- Qualitätssicherung

Ihr Profil:
- Abgeschlossenes Studium der Elektrotechnik
- Mindestens 3 Jahre Berufserfahrung
- Deutsch und Englisch fließend

Wir bieten:
- Attraktives Gehalt
- Flexible Arbeitszeiten
- Weiterbildungsmöglichkeiten

Bei Interesse senden Sie Ihre Bewerbung an:
Frau Schmidt
personal@techfirma.ch"#
  }
}

test MinimalJobOfferExtractionTest {
  functions [ExtractJobOffer]
  args {
    webpage_text #"Développeur Web - Lausanne

Nous recherchons un développeur web pour rejoindre notre équipe.

Tâches principales:
- Développement frontend et backend
- Maintenance de sites existants

Compétences requises:
- HTML, CSS, JavaScript
- PHP ou Python

Envoyez votre CV à info@webdev.ch"#
  }
}