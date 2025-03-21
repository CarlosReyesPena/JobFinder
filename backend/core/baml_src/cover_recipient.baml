// resume.baml - BAML file for structured cover letter generation and structured outputs

// Structured output class for Cover Letters
class CoverLetterRecipient {
  company_name string? @description("Name of the company if available in the job description") @assert(valid_length, {{ this|length <= 26 }})
  recipient_name string? @description("Name and title of the recipient if known") @assert(valid_length, {{ this|length <= 26 }})
  generic_greeting string? @description("Generic greeting to use if no specific recipient is identified (e.g., 'À qui de droit')") @assert(valid_length, {{ this|length <= 26 }})
  address_lines string[]? @description("Address lines extracted from the job description") @assert(valid_length, {{ this|length <= 26 }})

  @@assert(mutually_exclusive_greeting, {{
    (this.recipient_name is not none and this.generic_greeting is none) or
    (this.recipient_name is none and this.generic_greeting is not none)
  }})
}

// Function for generating a cover letter recipient section
function GenerateCoverRecipient(
  job_description: string @assert(not_empty, {{ this|length > 0 }})
) -> CoverLetterRecipient {
  client LLMFallback
  prompt #"# Cover Letter Recipient Information Extraction

## Task
Extract the recipient information for a cover letter from the provided job description. This information will be used as the formal address section at the top of a cover letter.

## Guidelines

1. **Company Information:**
   - Extract the exact company name as mentioned in the job description.
   - Do not invent or assume company names if not explicitly stated.
   - If the company name is not mentioned, leave this field empty.

2. **Recipient Information:**
   - If a specific person is mentioned (e.g., "Contact: Laura Rudaz-Truscello"), extract their lastname and determine the appropriate title:
     * For feminine first names (e.g., Laura, Marie, Sophie), use "Madame"
     * For masculine first names (e.g., Jean, Pierre, Marc), use "Monsieur"
     * If unsure about the gender, do not add a title
   - If no specific person is mentioned, use ONLY the appropriate generic greeting based on the language:
     * French: "À qui de droit" (NEVER use "Madame, Monsieur" or other variations)
     * German: "Für wen es gilt" (NEVER use "Sehr geehrte Damen und Herren" or other variations)
     * English: "To Whom It May Concern" (NEVER use "Dear Sir or Madam" or other variations)
   - NEVER combine generic greetings with specific names
   - NEVER use multiple greetings or variations

3. **Address:**
   - Extract the full address exactly as mentioned, ensuring correct formatting.
   - Include all address components in the address_lines array:
     * Street and building number
     * Postal code and city
   - If no address is provided, leave address_lines empty
   - Do not include email addresses in the address_lines

## Critical Rules
- **Accuracy is critical:** All extracted information must be factually correct.
- **Do not invent missing details:** If information is unavailable, leave the corresponding fields empty.
- **No placeholders:** Never use placeholders like "[Company Name]" or "[Address]".
- **Language sensitivity:** Adapt the generic greeting to match the language of the job description.
- **Format for direct use:** The output should be ready for direct insertion into a formal cover letter.
- **Single greeting rule:** Use either a specific recipient name OR a generic greeting, never both.
- **No variations:** Use only the exact generic greetings specified above for each language.


Job Description:
{{ job_description }}

{# special macro to print the output schema instructions #}
{{ ctx.output_format }}
"#
}

// Optional tests for the function
test CoverRecipientTest {
  functions [GenerateCoverRecipient]
  args {
    job_description #"Vous êtes ingénieur.e de projet en électricité ? Vous possédez une expérience en Suisse ? Alors n'hésitez plus et postulez !

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

test CoverRecipientWithAddressTest {
  functions [GenerateCoverRecipient]
  args {
    job_description #"Nettoyeurs SA recherche un technicien en nettoyage industriel

Nettoyeurs SA, entreprise leader dans le domaine du nettoyage industriel, recherche un technicien qualifié pour rejoindre son équipe à Lausanne.

Responsabilités:
- Effectuer des nettoyages techniques dans des environnements industriels
- Manipuler des équipements spécialisés
- Respecter les normes de sécurité et d'hygiène

Profil recherché:
- Formation technique ou expérience équivalente
- Permis de conduire
- Autonomie et rigueur

Nous offrons:
- Un salaire compétitif
- Des formations continues
- Un environnement de travail dynamique

Veuillez envoyer votre candidature à:
Nettoyeurs SA
Monsieur Jean Dupont
Rue de l'Industrie 45
1020 Renens

Ou par email: recrutement@nettoyeurs-sa.ch"#
  }
}

test CoverRecipientGermanTest {
  functions [GenerateCoverRecipient]
  args {
    job_description #"Stellenangebot: Elektroingenieur/in

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

test CoverRecipientMinimalFrenchTest {
  functions [GenerateCoverRecipient]
  args {
    job_description #"Offre d'emploi : Développeur Full Stack

Nous recherchons un développeur full stack expérimenté pour rejoindre notre équipe.

Profil recherché :
- 3+ ans d'expérience en développement web
- Maîtrise des technologies modernes (React, Node.js, Python)
- Capacité à travailler en équipe

Avantages :
- Télétravail possible
- Environnement dynamique
- Formation continue

Envoyez votre candidature à : recrutement@techcompany.ch"#
  }
}

test CoverRecipientMinimalEnglishTest {
  functions [GenerateCoverRecipient]
  args {
    job_description #"Job Opening: Full Stack Developer

We are looking for an experienced full stack developer to join our team.

Required Profile:
- 3+ years of web development experience
- Mastery of modern technologies (React, Node.js, Python)
- Team player mindset

Benefits:
- Remote work possible
- Dynamic environment
- Continuous training

Send your application to: careers@techcompany.com"#
  }
}

test CoverRecipientNoNameNoAddressFrenchTest {
  functions [GenerateCoverRecipient]
  args {
    job_description #"Ingénieur en Automatisation - Yverdon-les-Bains

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

test CoverRecipientNoNameNoAddressEnglishTest {
  functions [GenerateCoverRecipient]
  args {
    job_description #"Automation Engineer - Zurich

Tech Solutions AG, a leader in industrial automation, is seeking a qualified engineer.

Responsibilities:
- Development of automation solutions
- Industrial process optimization
- Technical customer support

Required Profile:
- Engineering degree in automation
- PLC programming experience
- Fluent in German and English

Benefits:
- Competitive salary
- Flexible working hours
- Modern equipment

Apply online through our recruitment platform."#
  }
}

test CoverRecipientNoCompanyNameTest {
  functions [GenerateCoverRecipient]
  args {
    job_description #"Offre d'emploi : Chef de Projet IT

Nous recherchons un chef de projet IT expérimenté pour notre équipe à Genève.

Missions :
- Gestion de projets IT complexes
- Coordination des équipes techniques
- Communication avec les clients

Profil recherché :
- 5+ ans d'expérience en gestion de projet
- Certifications PMP ou Prince2
- Français et anglais courant

Avantages :
- Package salarial attractif
- Formation continue
- Environnement international

Envoyez votre candidature à :
Monsieur Pierre Martin
Rue du Commerce 123
1200 Genève

Ou par email : jobs@company.ch"#
  }
}