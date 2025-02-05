// resume.baml - BAML file for structured cover letter generation and structured outputs

// Structured output class for Cover Letters
class CoverLetterResponse {
  subject string
  greeting string
  introduction string
  skills_experience string @description("Section for skills and experience")
  motivation string
  conclusion string
  closing string
}

// Function for generating a cover letter with a reference letter style prompt
function GenerateCoverLetterWithReference(
  user_profile: string,
  job_description: string,
  reference_letter: string
) -> CoverLetterResponse {
  client Ollama
  prompt #"
    {# 1. Goals of the Cover Letter
   **Emulate the Human Writing Style of the Reference Letter**
   - Analyze its sentence flow, tone, and word choices.
   - Adopt the same warmth, fluency, and persuasiveness in this new context.
   - Be mindful to create a fresh piece of writing that is never a direct copy.

   **Craft a Personalized, High-Impact Cover Letter**
   - Align with Swiss business norms: concise, respectful, and polished.
   - Present concrete examples of the candidate's skills, achievements, and relevant experiences.
   - Draw clear connections between the candidate's background and the target role's demands.
   - Conclude with an engaging call to action that shows the candidate's readiness to move forward.

2. Critical Constraints
   **No Placeholders**
   - Avoid placeholders like "[Your Name]" or "[Company Name]." Instead, integrate genuine details as provided about the candidate and the company.

   **No Direct Copying or Paraphrasing from the Reference Letter**
   - Use the reference only for stylistic inspiration—do not replicate specific sentences or phrases.

   **Adhere to Swiss Professional Standards**
   - Remain polite, professional, and respectful, consistent with formal business etiquette in Switzerland.

   **Optimize for Recruiter Readability**
   - Ensure clarity, logical flow, and a persuasive yet natural tone. The letter should feel genuinely human-authored.

   **No False Claims**
   - Emphasize real accomplishments and strengths. Avoid exaggeration or fabrication.

3. Style Guidelines
   **Be Specific About Achievements and Skills**
   - Provide real, relevant examples of accomplishments, showcasing the candidate's expertise.

   **Use Active Voice**
   - Prefer formulations like "I led," "I achieved," "I contributed" over passive statements.

   **Demonstrate Knowledge of the Company and Role**
   - Reference genuine details about the company's values or objectives to underscore genuine interest.

   **Maintain a Professional, Confident Tone**
   - Express self-assurance without appearing boastful or arrogant.

   **Balance Enthusiasm and Professionalism**
   - Sound genuinely excited about the position but stay within a polished, respectful tone.

   **Avoid Generic or Repetitive Phrasing**
   - Keep the language lively and precise; avoid clichés or overused expressions.

4. Conclusion
   - End with a culturally appropriate closing, depending on the language context (e.g., "Yours sincerely," "Mit freundlichen Grüßen," or "Je vous prie d'agréer, Madame, Monsieur, mes salutations distinguées.").
   - Refrain from including placeholder names or references to the candidate's identity.
   - The final text must be perceived as authentically human-written and fully original.

**Final Note:**
- Do not directly copy or translate phrases from the reference letter.
- Incorporate the candidate's real experiences in a way that highlights their strengths truthfully.
- Each word should be chosen thoughtfully to ensure the letter is both persuasive and genuine.
- Your cover letter should stand on its own as a unique document, ready for immediate use by the candidate.
- The letter should be in the language of the job description.
 #}

    Candidate Profile:
    {{ user_profile }}

    Job Description:
    {{ job_description }}

    Reference Letter:
    {{ reference_letter }}

    {# special macro to print the output schema instructions #}
    {{ ctx.output_format }}
  "#
}

// Function for generating a cover letter without a reference letter style prompt
function GenerateCoverLetter(
  user_profile: string,
  job_description: string
) -> CoverLetterResponse {
  client Ollama
  prompt #"
    {## 1. Goals of the Cover Letter

## Produce a High-Impact, Personalized Letter
- Highlight the candidate's relevant skills and accomplishments.
- Clearly connect these attributes to the requirements of the target position.
- Include a compelling introduction and a concise, persuasive conclusion.

## Embody Professional Swiss Business Etiquette
- Ensure the language is respectful, polished, and appropriately formal.
- Maintain a tone that is confident without sounding boastful.
- Use active voice to demonstrate responsibility and ownership of past achievements.

## Engage the Recruiter
- Write in a way that is both clear and captivating.
- Incorporate real, quantifiable examples where possible.
- End with a clear call to action expressing eagerness to discuss the role further.

---

# 2. Critical Constraints

### No Placeholders
- Do not insert placeholders such as `[Company Name]` or `[Position Title] or anything like that.`
  Replace them with authentic information or omit them if unknown.

### No Copying from External Sources
- All content must be original—avoid any direct quotes or paraphrased text from existing letters or external references.

### Adherence to Swiss Professional Standards
- Employ a polite, formal tone that aligns with typical Swiss business communication.

### Optimize Readability
- Make sure each paragraph is clear and purposeful.
  The document should feel cohesive and flow logically from one idea to the next.

---

# 3. Style Guidelines

## Use Active Voice
- Favor constructions such as **"I led,"** **"I managed,"** or **"I increased,"** rather than passive formulations.

## Highlight Specific Achievements
- Provide concrete examples that demonstrate the candidate's skills and accomplishments.
- Where possible, quantify outcomes (e.g., **"increased sales by 20%").

## Demonstrate Knowledge of the Role and Company
- Reference any known details about the employer's mission, values, or recent projects.
- Show enthusiasm and genuine interest in contributing to the company's goals.

## Maintain a Polite, Confident Tone
- Show self-assurance without excessive self-praise.
- Keep the tone positive and forward-looking.

## Balance Formality and Warmth
- Sound approachable while respecting professional standards.
- Avoid overly casual or overly stiff language.

## Conclude with a Formal Closing
- End with a culturally appropriate sign-off, such as:
  **"Yours sincerely,"**
  **"Mit freundlichen Grüßen,"**
  **"Je vous prie d'agréer, Madame, Monsieur, mes salutations distinguées."**

---

# Final Note
The finished letter should read as if it was personally drafted by a real individual.
It must be well-structured, honest about the candidate's experiences, and crafted to maximize the candidate's appeal for the position.
Ensure each sentence flows naturally and that no generic or unsubstantiated claims are made.
Each word should be chosen thoughtfully to ensure the letter is both persuasive and genuine.
The letter should be in the language of the job description.
#}


    Candidate Profile:
    {{ user_profile }}

    Job Description:
    {{ job_description }}

    {# special macro to print the output schema instructions #}
    {{ ctx.output_format }}
  "#
}

// Optional tests for the functions

test CoverLetterWithReferenceTest {
  functions [GenerateCoverLetterWithReference]
  args {
    user_profile #"profil_personnel:
                    description: >
                      Passionné par la technologie et l’électronique, je suis animé par la programmation et l’innovation.
                      Doté d’une excellente communication, je prospère autant en équipe qu’en autonomie et suis motivé
                      par la résolution de défis complexes dans ce domaine en constante évolution.

                  projets:
                    - name: JobFinder – Plateforme d’automatisation des candidatures
                      location: Suisse
                      position: Développeur et responsable de projet
                      start_date: 2024-09
                      end_date: present
                      highlights:
                        - Développement d’une application pour automatiser la gestion des offres d’emploi, le suivi des candidatures, et la génération automatisée de documents personnalisés.
                        - Mise en œuvre d’une architecture modulaire incluant un backend FastAPI et une base de données SQLite.
                        - Intégration d’APIs (OpenAI) pour générer des lettres de motivation adaptées aux offres.
                        - Technologies utilisées : Python, SQLModel, FastAPI, Playwright, OpenAI API, Git.
                        - Déploiement sur GitHub pour gestion collaborative et suivi des versions.
                    - name: Plateforme d’Automatisation pour l’Analyse de Données Professionnelles
                      location: Vaud, Suisse
                      position: Développeur de projet
                      start_date: 2024-02
                      end_date: 2024-08
                      highlights:
                        - Développement d’un programme autonome en Python pour la collecte et la catégorisation des données d’entreprises, intégrant des APIs d’IA.
                        - Technologies utilisées : Python, Intégration d’IA, APIs LLM, Git, LaTeX, Technologies Web, Multi-threading asynchrone.

                  experiences:
                    - company: Centre vaudois d’aide à la jeunesse (CVAJ) et Appuis apprentis (AppApp)
                      location: Vaud, Suisse
                      position: Répétiteur en sciences et programmation
                      start_date: 2022
                      end_date: 2024
                      highlights:
                        - Cours particuliers en mathématiques, physique, programmation Java, et électrotechnique.
                        - Aide à la compréhension des concepts complexes et accompagnement personnalisé.
                    - company: Gets MMS SA
                      location: Lausanne, Suisse
                      position: Développeur WiFi et audio
                      start_date: 2019
                      end_date: 2019
                      highlights:
                        - Conception d’un système Mesh Wi-Fi pour la transmission audio.
                        - Assemblage et test de prototypes pour valider la performance du réseau.

                  formation:
                    - institution: Haute École d’Ingénieurs d’Yverdon
                      area: Automatisation industrielle et Informatique embarquée
                      start_date: 2020-09
                      end_date: 2024-03
                      highlights:
                        - Maîtrise des systèmes électroniques embarqués, de la conception à la programmation.
                    - institution: Ecole de métiers de Lausanne – Ecole supérieure
                      area: Diplôme en génie électrique – électronique embarquée
                      start_date: 2018-05
                      end_date: 2020-05
                      highlights:
                        - Conception et développement d’un émetteur audio Wi-Fi pour transmission en temps réel vers deux récepteurs.
                    - institution: Ecole de métiers de Lausanne
                      area: CFC en électronique
                      start_date: 2014-04
                      end_date: 2018-04
                      highlights:
                        - Capacité à construire et à réparer des circuits électroniques, à souder des composants et à utiliser des outils de coupe et de soudure.

                  competences:
                    - label: Programmation
                      details: C/C++, Python, C#, Java, VHDL, LaTex
                    - label: Divers
                      details: STM32, Espressif ESP32, Altium, Logisim, Service clientèle
                    - label: Langues
                      details:
                        - Français : C2 (niveau de compétence maximum)
                        - Anglais : B2 (niveau de compétence intermédiaire avancé)
                        - Espagnol : Langue maternelle (niveau de compétence maximum)"#
    job_description #"Junior Technician - Electrotechnician (SY-EPC-OMS-2025-10-GRAE)
                      CERN European Organization for Nuclear Research
                      Postuler
                      Sauvegarder l'emploi
                      Date de publication :24 janvier 2025
                      Lieu de travail :Geneva

                      Job Description

                      The Electrical Power Converter
                      (EPC) Group, responsible for delivering power converters for the High Luminosity LHC Project (HL-LHC) and POPS+, is looking for a motivated Electrotechnical Technician to join our team. In this role, you will have the unique opportunity to work on innovative technology, taking a critical role in helping to build power converters that will power one of the world's most advanced scientific machines.

                      Your responsibilities

                      The Electrical Power Converter (EPC) Group, responsible for delivering power converters across CERN accelerator complex, is looking for a motivated Electrotechnical Technician to join our team.

                      In this role, you will have a critical role in building power converters that will power one of the world's most advanced scientific machines.

                      What you will do:

                      Participate in the assembly of equipment in converters, in the wiring and assembly of hydraulic cooling systems for power converters.
                      Organize the logistics of activities.
                      Communicate problems encountered to project managers and participate in their resolutions.
                      Document activities and their status with equipment managers by specifying modifications or improvements during the assembly process.
                      This team collaboration will allow the technician to acquire first enriching electromechanical experience in view of the variety of fields (mechanics, assembly mechanics, wiring, piping, management, etc.).

                      More information here: https://videos.cern.ch/record/2688929

                      Your profile

                      Use of CAD tools (2D, 3D) for the creation of simple electromechanical assemblies. Manufacture, assembly or installation of electromechanical assemblies

                      Skills

                      Previous experience within an electrical/electro-mechanical assembly role
                      Ability to use machine tools
                      Ability to use schematics and assembly drawings
                      Ability to Write Clear, Concise Technical Reports (using office
                      tools)
                      Attention to detail
                      Fluent in French, the ability to work in English would be an advantage.

                      Eligibility criteria:

                      You are a national of a CERN Member or Associate Member State
                      .
                      By the application deadline, you have a maximum of two years of professional experience since graduation in TECHNICIEN EN ELECTROMECANIQUE (or a related field) and your highest educational qualification is a general secondary education diploma.
                      You have never had a CERN fellow or graduate contract before.
                      Applicants with a Bachelor's, Master's or PhD degree are not eligible.

                      Additional Information

                      Job closing date: 23rd of February 2025 at 23:59 CET.

                      Contract duration: 24 months, with a possible extension up to 36 months maximum.

                      Working hours: 40 hours per week

                      Job flexibility: Fully Onsite

                      Target start date: 01-April-2025

                      This position involves:

                      Work in Radiation Areas.
                      Interventions in underground installations.
                      A valid driving licence.
                      Use of certain mobile work equipment or equipment used for lifting loads (lifting equipment, bridge cranes, aerial work platforms, etc.) requiring a driving authorization.

                      Given the occupational health risks associated with this position, the selected candidate must obtain medical clearance before a contract offer is confirmed.

                      Job reference: SY-EPC-OMS-2025-10-GRAE

                      Field of work: Electrical or Electronics Engineering

                      Benchmark job: 300050 - Electromechanical Technician

                      What we offer

                      A monthly stipend of 4624  Swiss Francs (net of tax).
                      Coverage by CERN's comprehensive health scheme (for yourself, your spouse and children), and membership of the CERN Pension Fund.
                      Depending on your individual circumstances: installation grant; family, child and infant allowances; payment of travel expenses at the beginning and end of contract.
                      30 days of paid leave per year.
                      On-the-job and formal training at CERN as well as in-house language courses for English and/or French.

                      About us

                      At CERN, the European Organization for Nuclear Research, physicists and engineers are probing the fundamental structure of the universe. Using the world's largest and most complex scientific instruments, they study the basic constituents of matter - fundamental particles that are made to collide together at close to the speed of light. The process gives physicists clues about how particles interact, and provides insights into the fundamental laws of nature. Find out more on http://home.cern.

                       

                      Diversity has been an integral part of CERN's mission since its foundation and is an established value of the Organization. Employing a diverse workforce is central to our success.



                      Postuler
                      Sauvegarder l'emploi
                      Signaler cette offre d'emploi
                      Autres recherches d’emplois
                      ingénieur mécanicien | opérateur de production | secrétaire médical | gestionnaire en intendance | assistante médicale | polymaintenicien | ingénieure mécanicienne | agent d exploitation | ingénieur mécanique | ingénieur biomédical | ingénieur civil | chargé de sécurité | ingénieur mécanicienne | dessinateur en bâtiment | electronicien | agent de sécurité | infirmier chef | employé de commerce | ingénieur | chef de cuisine
                      Catégories:
                      Immobilier, Services techniques / Concierge"#
    reference_letter #" This is a reference letter.
    

                        Sujet : Candidature pour un poste de formateur au CEFIL
                        Monsieur Geinoz,
                        Depuis toujours passionné par les technologies et les interactions sociales, j'ai longtemps rêvé
                        d'enseigner l'électronique. Votre offre d'emploi représente pour moi une opportunité précieuse de
                        me rapprocher de cet objectif. Je suis titulaire d'un CFC en électronique et d'un diplôme de
                        technicien en génie électrique. Depuis deux ans, j'ai également donné des cours
                        d’électronique, d’électricité, de programmation et d’autres matières, ce qui m’a permis
                        d’améliorer mes compétences pédagogiques. Pour moi, cette opportunité d'emploi est une
                        façon d'atteindre mes objectifs professionnels et personnels.
                        Durant ma formation en électronique, j'ai réalisé des projets nécessitant une très bonne gestion
                        de projet, tels qu'un interphone Wi-Fi Mesh et un système de vision augmentée pour évaluer
                        en temps réel l'équilibre d’une personne. Mon sens analytique et objectif m’a toujours permis
                        d’emprunter la voie la plus optimale pour la réalisation de ces projets. Par ailleurs, mes
                        expériences en soutien scolaire avec le CVAJ et AppApp ont renforcé mon intérêt pour la
                        pédagogie. J’ai rapidement acquis et mis en pratique des notions clés de l'enseignement, et
                        j'ai toujours su m’adapter aux besoins de mes élèves, les accompagnant avec bienveillance et
                        rigueur.
                        Très attentif aux aspects sociaux et humains, j'analyse les situations de manière objective,
                        en tenant compte des biais sociaux et autres facteurs, ce qui me permet d'agir de manière
                        empathique et objective, ce qui me serait utile dans l'accompagnement des personnes en
                        réinsertion professionnelle. Depuis l’arrêt de mon bachelor, je me consacre à un projet personnel
                        intégrant l'IA afin d’analyser le profil des entreprises et donc aider dans la recherche d’emplois.
                        Fort de mes connaissances en électronique et en informatique, ainsi que de ma passion pour les
                        sciences sociales et l'enseignement, je suis convaincu de pouvoir apporter une réelle valeur au
                        CEFIL dans sa mission.
                        Je serais honoré de mettre mon savoir-faire et mon engagement au service de votre équipe et
                        de contribuer activement à la mission du CEFIL. Dans l’attente de pouvoir échanger avec vous,
                        je vous prie d'agréer, Monsieur Geinoz, mes salutations distinguées."#
  }
}

test CoverLetterTest {
  functions [GenerateCoverLetter]
  args {
    user_profile #"profil_personnel:
                    description: >
                      Passionné par la technologie et l’électronique, je suis animé par la programmation et l’innovation.
                      Doté d’une excellente communication, je prospère autant en équipe qu’en autonomie et suis motivé
                      par la résolution de défis complexes dans ce domaine en constante évolution.

                  projets:
                    - name: JobFinder – Plateforme d’automatisation des candidatures
                      location: Suisse
                      position: Développeur et responsable de projet
                      start_date: 2024-09
                      end_date: present
                      highlights:
                        - Développement d’une application pour automatiser la gestion des offres d’emploi, le suivi des candidatures, et la génération automatisée de documents personnalisés.
                        - Mise en œuvre d’une architecture modulaire incluant un backend FastAPI et une base de données SQLite.
                        - Intégration d’APIs (OpenAI) pour générer des lettres de motivation adaptées aux offres.
                        - Technologies utilisées : Python, SQLModel, FastAPI, Playwright, OpenAI API, Git.
                        - Déploiement sur GitHub pour gestion collaborative et suivi des versions.
                    - name: Plateforme d’Automatisation pour l’Analyse de Données Professionnelles
                      location: Vaud, Suisse
                      position: Développeur de projet
                      start_date: 2024-02
                      end_date: 2024-08
                      highlights:
                        - Développement d’un programme autonome en Python pour la collecte et la catégorisation des données d’entreprises, intégrant des APIs d’IA.
                        - Technologies utilisées : Python, Intégration d’IA, APIs LLM, Git, LaTeX, Technologies Web, Multi-threading asynchrone.

                  experiences:
                    - company: Centre vaudois d’aide à la jeunesse (CVAJ) et Appuis apprentis (AppApp)
                      location: Vaud, Suisse
                      position: Répétiteur en sciences et programmation
                      start_date: 2022
                      end_date: 2024
                      highlights:
                        - Cours particuliers en mathématiques, physique, programmation Java, et électrotechnique.
                        - Aide à la compréhension des concepts complexes et accompagnement personnalisé.
                    - company: Gets MMS SA
                      location: Lausanne, Suisse
                      position: Développeur WiFi et audio
                      start_date: 2019
                      end_date: 2019
                      highlights:
                        - Conception d’un système Mesh Wi-Fi pour la transmission audio.
                        - Assemblage et test de prototypes pour valider la performance du réseau.

                  formation:
                    - institution: Haute École d’Ingénieurs d’Yverdon
                      area: Automatisation industrielle et Informatique embarquée
                      start_date: 2020-09
                      end_date: 2024-03
                      highlights:
                        - Maîtrise des systèmes électroniques embarqués, de la conception à la programmation.
                    - institution: Ecole de métiers de Lausanne – Ecole supérieure
                      area: Diplôme en génie électrique – électronique embarquée
                      start_date: 2018-05
                      end_date: 2020-05
                      highlights:
                        - Conception et développement d’un émetteur audio Wi-Fi pour transmission en temps réel vers deux récepteurs.
                    - institution: Ecole de métiers de Lausanne
                      area: CFC en électronique
                      start_date: 2014-04
                      end_date: 2018-04
                      highlights:
                        - Capacité à construire et à réparer des circuits électroniques, à souder des composants et à utiliser des outils de coupe et de soudure.

                  competences:
                    - label: Programmation
                      details: C/C++, Python, C#, Java, VHDL, LaTex
                    - label: Divers
                      details: STM32, Espressif ESP32, Altium, Logisim, Service clientèle
                    - label: Langues
                      details:
                        - Français : C2 (niveau de compétence maximum)
                        - Anglais : B2 (niveau de compétence intermédiaire avancé)
                        - Espagnol : Langue maternelle (niveau de compétence maximum)"#
    job_description #"Junior Technician - Electrotechnician (SY-EPC-OMS-2025-10-GRAE)
                      CERN European Organization for Nuclear Research
                      Postuler
                      Sauvegarder l'emploi
                      Date de publication :24 janvier 2025
                      Lieu de travail :Geneva

                      Job Description

                      The Electrical Power Converter
                      (EPC) Group, responsible for delivering power converters for the High Luminosity LHC Project (HL-LHC) and POPS+, is looking for a motivated Electrotechnical Technician to join our team. In this role, you will have the unique opportunity to work on innovative technology, taking a critical role in helping to build power converters that will power one of the world's most advanced scientific machines.

                      Your responsibilities

                      The Electrical Power Converter (EPC) Group, responsible for delivering power converters across CERN accelerator complex, is looking for a motivated Electrotechnical Technician to join our team.

                      In this role, you will have a critical role in building power converters that will power one of the world's most advanced scientific machines.

                      What you will do:

                      Participate in the assembly of equipment in converters, in the wiring and assembly of hydraulic cooling systems for power converters.
                      Organize the logistics of activities.
                      Communicate problems encountered to project managers and participate in their resolutions.
                      Document activities and their status with equipment managers by specifying modifications or improvements during the assembly process.
                      This team collaboration will allow the technician to acquire first enriching electromechanical experience in view of the variety of fields (mechanics, assembly mechanics, wiring, piping, management, etc.).

                      More information here: https://videos.cern.ch/record/2688929

                      Your profile

                      Use of CAD tools (2D, 3D) for the creation of simple electromechanical assemblies. Manufacture, assembly or installation of electromechanical assemblies

                      Skills

                      Previous experience within an electrical/electro-mechanical assembly role
                      Ability to use machine tools
                      Ability to use schematics and assembly drawings
                      Ability to Write Clear, Concise Technical Reports (using office
                      tools)
                      Attention to detail
                      Fluent in French, the ability to work in English would be an advantage.

                      Eligibility criteria:

                      You are a national of a CERN Member or Associate Member State
                      .
                      By the application deadline, you have a maximum of two years of professional experience since graduation in TECHNICIEN EN ELECTROMECANIQUE (or a related field) and your highest educational qualification is a general secondary education diploma.
                      You have never had a CERN fellow or graduate contract before.
                      Applicants with a Bachelor's, Master's or PhD degree are not eligible.

                      Additional Information

                      Job closing date: 23rd of February 2025 at 23:59 CET.

                      Contract duration: 24 months, with a possible extension up to 36 months maximum.

                      Working hours: 40 hours per week

                      Job flexibility: Fully Onsite

                      Target start date: 01-April-2025

                      This position involves:

                      Work in Radiation Areas.
                      Interventions in underground installations.
                      A valid driving licence.
                      Use of certain mobile work equipment or equipment used for lifting loads (lifting equipment, bridge cranes, aerial work platforms, etc.) requiring a driving authorization.

                      Given the occupational health risks associated with this position, the selected candidate must obtain medical clearance before a contract offer is confirmed.

                      Job reference: SY-EPC-OMS-2025-10-GRAE

                      Field of work: Electrical or Electronics Engineering

                      Benchmark job: 300050 - Electromechanical Technician

                      What we offer

                      A monthly stipend of 4624  Swiss Francs (net of tax).
                      Coverage by CERN's comprehensive health scheme (for yourself, your spouse and children), and membership of the CERN Pension Fund.
                      Depending on your individual circumstances: installation grant; family, child and infant allowances; payment of travel expenses at the beginning and end of contract.
                      30 days of paid leave per year.
                      On-the-job and formal training at CERN as well as in-house language courses for English and/or French.

                      About us

                      At CERN, the European Organization for Nuclear Research, physicists and engineers are probing the fundamental structure of the universe. Using the world's largest and most complex scientific instruments, they study the basic constituents of matter - fundamental particles that are made to collide together at close to the speed of light. The process gives physicists clues about how particles interact, and provides insights into the fundamental laws of nature. Find out more on http://home.cern.

                       

                      Diversity has been an integral part of CERN's mission since its foundation and is an established value of the Organization. Employing a diverse workforce is central to our success.



                      Postuler
                      Sauvegarder l'emploi
                      Signaler cette offre d'emploi
                      Autres recherches d’emplois
                      ingénieur mécanicien | opérateur de production | secrétaire médical | gestionnaire en intendance | assistante médicale | polymaintenicien | ingénieure mécanicienne | agent d exploitation | ingénieur mécanique | ingénieur biomédical | ingénieur civil | chargé de sécurité | ingénieur mécanicienne | dessinateur en bâtiment | electronicien | agent de sécurité | infirmier chef | employé de commerce | ingénieur | chef de cuisine
                      Catégories:
                      Immobilier, Services techniques / Concierge"#
  }
}
