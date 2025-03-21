// resume.baml - BAML file for structured cover letter generation and structured outputs

// Structured output class for Cover Letters
class CoverLetterBody {
  subject string @description("The subject line of the cover letter") @assert(valid_length, {{ this|length >= 5 and this|length <= 52 }})
  greeting string @description("The greeting line of the cover letter") @assert(valid_length, {{ this|length >= 5 and this|length <= 35 }})
  introduction string @description("The opening paragraph introducing the candidate") @assert(valid_length, {{ this|length >= 50 and this|length <= 600 }})
  skills_experience string @description("Section highlighting relevant skills and experience") @assert(valid_length, {{ this|length >= 100 and this|length <= 600 }})
  motivation string @description("Section explaining motivation and fit for the role") @assert(valid_length, {{ this|length >= 100 and this|length <= 600 }})
  conclusion string @description("The closing paragraph of the cover letter") @assert(valid_length, {{ this|length >= 50 and this|length <= 300 }})
  closing string @description("The formal closing line") @assert(valid_length, {{ this|length >= 20 and this|length <= 100 }})

  @@assert(total_length, {{
    (this.subject|length + this.greeting|length + this.introduction|length +
     this.skills_experience|length + this.motivation|length + this.conclusion|length +
     this.closing|length) <= 2200
  }})
}

// Function for generating a cover letter with a reference letter style prompt
function GenerateCoverLetter(
  user_profile: string @assert(not_empty, {{ this|length > 0 }}),
  job_description: string @assert(not_empty, {{ this|length > 0 }}),
  reference_letter: string?
) -> CoverLetterBody {
  client LLMFallback
  prompt #"1. Core Principles for an Outstanding Cover Letter

Focus on Value Proposition
- Identify the 2-3 most relevant skills/experiences that directly match the job requirements
- Present concrete achievements with measurable impact
- Connect your experience to specific needs mentioned in the job description

Strategic Structure
- Opening: Grab attention with a strong value proposition
- Body: Focus on 2-3 key achievements that demonstrate required skills
- Closing: End with a clear call to action

Language and Tone
- Use active voice and strong action verbs
- Be specific and concise - avoid generic statements
- Maintain professional yet engaging tone
- Adapt closing formula based on language:
  * French: "Je vous prie d'agréer, Madame/Monsieur, mes salutations distinguées"
  * English: "Yours sincerely" or "Best regards"
  * German: "Mit freundlichen Grüßen"

2. Critical Rules
- No placeholders or generic text
- No copying from reference letter (if provided)
- No false claims or exaggerations
- Maximum total length: 2200 characters
- Each section must be properly sized:
  * Subject: 5-52 characters
  * Greeting: 5-35 characters
  * Introduction: 50-600 characters
  * Skills/Experience: 100-600 characters
  * Motivation: 100-600 characters
  * Conclusion: 50-200 characters
  * Closing: 20-100 characters

3. Content Guidelines
{% if reference_letter %}
Reference Letter Style Analysis:
- Study the writing style, tone, and structure
- Adapt similar warmth and professionalism
- Never copy specific phrases
{% endif %}

Key Focus Areas:
- Match job requirements with specific examples
- Highlight quantifiable achievements
- Demonstrate understanding of the role
- Show enthusiasm for the company/position
- Keep paragraphs focused and concise

4. Quality Checks
- Verify all sections meet length requirements
- Ensure proper paragraph flow
- Check for professional language
- Confirm no placeholders remain
- Validate closing formula matches language

Candidate Profile:
{{ user_profile }}

{% if reference_letter %}
Reference Letter:
{{ reference_letter }}
{% endif %}

Job Description:
{{ job_description }}

{# special macro to print the output schema instructions #}
{{ ctx.output_format }}
"#
}

// Optional tests for the functions

test CoverLetterWithReferenceTest {
  functions [GenerateCoverLetter]
  args {
    user_profile #"profil_personnel:
                    description: >
                      Passionné par la technologie et l'électronique, je suis animé par la programmation et l'innovation.
                      Doté d'une excellente communication, je prospère autant en équipe qu'en autonomie et suis motivé
                      par la résolution de défis complexes dans ce domaine en constante évolution.

                  projets:
                    - name: JobFinder – Plateforme d'automatisation des candidatures
                      location: Suisse
                      position: Développeur et responsable de projet
                      start_date: 2024-09
                      end_date: present
                      highlights:
                        - Développement d'une application pour automatiser la gestion des offres d'emploi, le suivi des candidatures, et la génération automatisée de documents personnalisés.
                        - Mise en œuvre d'une architecture modulaire incluant un backend FastAPI et une base de données SQLite.
                        - Intégration d'APIs (OpenAI) pour générer des lettres de motivation adaptées aux offres.
                        - Technologies utilisées : Python, SQLModel, FastAPI, Playwright, OpenAI API, Git.
                        - Déploiement sur GitHub pour gestion collaborative et suivi des versions.
                    - name: Plateforme d'Automatisation pour l'Analyse de Données Professionnelles
                      location: Vaud, Suisse
                      position: Développeur de projet
                      start_date: 2024-02
                      end_date: 2024-08
                      highlights:
                        - Développement d'un programme autonome en Python pour la collecte et la catégorisation des données d'entreprises, intégrant des APIs d'IA.
                        - Technologies utilisées : Python, Intégration d'IA, APIs LLM, Git, LaTeX, Technologies Web, Multi-threading asynchrone.

                  experiences:
                    - company: Centre vaudois d'aide à la jeunesse (CVAJ) et Appuis apprentis (AppApp)
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
                        - Conception d'un système Mesh Wi-Fi pour la transmission audio.
                        - Assemblage et test de prototypes pour valider la performance du réseau.

                  formation:
                    - institution: Haute École d'Ingénieurs d'Yverdon
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
                        - Conception et développement d'un émetteur audio Wi-Fi pour transmission en temps réel vers deux récepteurs.
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
    reference_letter #" This is a reference letter.


                        Sujet : Candidature pour un poste de formateur au CEFIL
                        Monsieur Geinoz,
                        Depuis toujours passionné par les technologies et les interactions sociales, j'ai longtemps rêvé
                        d'enseigner l'électronique. Votre offre d'emploi représente pour moi une opportunité précieuse de
                        me rapprocher de cet objectif. Je suis titulaire d'un CFC en électronique et d'un diplôme de
                        technicien en génie électrique. Depuis deux ans, j'ai également donné des cours
                        d'électronique, d'électricité, de programmation et d'autres matières, ce qui m'a permis
                        d'améliorer mes compétences pédagogiques. Pour moi, cette opportunité d'emploi est une
                        façon d'atteindre mes objectifs professionnels et personnels.
                        Durant ma formation en électronique, j'ai réalisé des projets nécessitant une très bonne gestion
                        de projet, tels qu'un interphone Wi-Fi Mesh et un système de vision augmentée pour évaluer
                        en temps réel l'équilibre d'une personne. Mon sens analytique et objectif m'a toujours permis
                        d'emprunter la voie la plus optimale pour la réalisation de ces projets. Par ailleurs, mes
                        expériences en soutien scolaire avec le CVAJ et AppApp ont renforcé mon intérêt pour la
                        pédagogie. J'ai rapidement acquis et mis en pratique des notions clés de l'enseignement, et
                        j'ai toujours su m'adapter aux besoins de mes élèves, les accompagnant avec bienveillance et
                        rigueur.
                        Très attentif aux aspects sociaux et humains, j'analyse les situations de manière objective,
                        en tenant compte des biais sociaux et autres facteurs, ce qui me permet d'agir de manière
                        empathique et objective, ce qui me serait utile dans l'accompagnement des personnes en
                        réinsertion professionnelle. Depuis l'arrêt de mon bachelor, je me consacre à un projet personnel
                        intégrant l'IA afin d'analyser le profil des entreprises et donc aider dans la recherche d'emplois.
                        Fort de mes connaissances en électronique et en informatique, ainsi que de ma passion pour les
                        sciences sociales et l'enseignement, je suis convaincu de pouvoir apporter une réelle valeur au
                        CEFIL dans sa mission.
                        Je serais honoré de mettre mon savoir-faire et mon engagement au service de votre équipe et
                        de contribuer activement à la mission du CEFIL. Dans l'attente de pouvoir échanger avec vous,
                        je vous prie d'agréer, Monsieur Geinoz, mes salutations distinguées."#
  }
}

test CoverLetterTest {
  functions [GenerateCoverLetter]
  args {
    user_profile #"profil_personnel:
                    description: >
                      Passionné par la technologie et l'électronique, je suis animé par la programmation et l'innovation.
                      Doté d'une excellente communication, je prospère autant en équipe qu'en autonomie et suis motivé
                      par la résolution de défis complexes dans ce domaine en constante évolution.

                  projets:
                    - name: JobFinder – Plateforme d'automatisation des candidatures
                      location: Suisse
                      position: Développeur et responsable de projet
                      start_date: 2024-09
                      end_date: present
                      highlights:
                        - Développement d'une application pour automatiser la gestion des offres d'emploi, le suivi des candidatures, et la génération automatisée de documents personnalisés.
                        - Mise en œuvre d'une architecture modulaire incluant un backend FastAPI et une base de données SQLite.
                        - Intégration d'APIs (OpenAI) pour générer des lettres de motivation adaptées aux offres.
                        - Technologies utilisées : Python, SQLModel, FastAPI, Playwright, OpenAI API, Git.
                        - Déploiement sur GitHub pour gestion collaborative et suivi des versions.
                    - name: Plateforme d'Automatisation pour l'Analyse de Données Professionnelles
                      location: Vaud, Suisse
                      position: Développeur de projet
                      start_date: 2024-02
                      end_date: 2024-08
                      highlights:
                        - Développement d'un programme autonome en Python pour la collecte et la catégorisation des données d'entreprises, intégrant des APIs d'IA.
                        - Technologies utilisées : Python, Intégration d'IA, APIs LLM, Git, LaTeX, Technologies Web, Multi-threading asynchrone.

                  experiences:
                    - company: Centre vaudois d'aide à la jeunesse (CVAJ) et Appuis apprentis (AppApp)
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
                        - Conception d'un système Mesh Wi-Fi pour la transmission audio.
                        - Assemblage et test de prototypes pour valider la performance du réseau.

                  formation:
                    - institution: Haute École d'Ingénieurs d'Yverdon
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
                        - Conception et développement d'un émetteur audio Wi-Fi pour transmission en temps réel vers deux récepteurs.
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
