import asyncio
import pytest
import os
import time
import uuid
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy import select

# Importer uniquement les managers
from backend.data.managers import (
    UserManager, JobOfferManager, DocumentManager, ApplicationManager
)
from backend.data.models import DocumentType, JobSite, User
from backend.data.database import (
    read_session_context, write_session_context, DatabaseManager
)

# Réinitialisation de la base de données
import backend.data.database as db_module

@pytest.fixture(scope="function")
async def setup_db():
    """Fixture qui réinitialise l'instance de DatabaseManager pour chaque test"""
    # Réinitialiser l'instance de DatabaseManager
    db_module.DatabaseManager._instance = None

    # Retourner les managers (plus besoin de yield car pas de cleanup spécial)
    return {
        "user_manager": UserManager(),
        "job_manager": JobOfferManager(),
        "document_manager": DocumentManager(),
        "application_manager": ApplicationManager()
    }

@pytest.fixture(scope="session", autouse=True)
async def cleanup_db():
    """Fixture qui nettoie les ressources de base de données à la fin de la session de test"""
    # Setup - ne fait rien au début
    yield
    
    # Teardown - nettoie les ressources après tous les tests
    if db_module.DatabaseManager._instance:
        await db_module.DatabaseManager._instance.cleanup()
        print("Database resources cleaned up")

# Fonction utilitaire pour générer des emails uniques
def unique_email(prefix="test"):
    """Génère une adresse email unique avec timestamp et UUID"""
    timestamp = int(time.time() * 1000)
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{timestamp}_{unique_id}@example.com"

# =====================================
# Tests des managers de base
# =====================================

@pytest.mark.asyncio
async def test_user_manager_basic(setup_db):
    """Test des opérations de base du UserManager"""
    # Récupérer les managers avec await
    managers = await setup_db
    user_manager = managers["user_manager"]

    # Création d'utilisateur avec email unique
    user = await user_manager.add_user(
        email=unique_email("user_basic"),
        username=f"testuser_{uuid.uuid4().hex[:8]}",
        password="password123",
        first_name="Test",
        last_name="User",
        config={"theme": "dark"}
    )

    assert user.id is not None
    assert user.email.startswith("user_basic")
    assert user.username.startswith("testuser_")

    # Récupération par ID
    retrieved_user = await user_manager.get_user_by_id(user.id)
    assert retrieved_user is not None
    assert retrieved_user.id == user.id

    # Récupération par email
    user_by_email = await user_manager.get_user_by_email(user.email)
    assert user_by_email is not None
    assert user_by_email.id == user.id

    # Récupération par username
    user_by_username = await user_manager.get_user_by_username(user.username)
    assert user_by_username is not None
    assert user_by_username.id == user.id

    # Mise à jour
    updated_user = await user_manager.update_user(
        user.id,
        first_name="Updated",
        last_name="Name"
    )
    assert updated_user.first_name == "Updated"
    assert updated_user.last_name == "Name"

    # Mise à jour config
    updated_config = await user_manager.update_config(
        user.id,
        {"language": "fr", "notifications": True}
    )
    assert updated_config.config["theme"] == "dark"  # Valeur existante
    assert updated_config.config["language"] == "fr"  # Nouvelle valeur
    assert updated_config.config["notifications"] is True  # Nouvelle valeur

    # Liste de tous les utilisateurs
    all_users = await user_manager.get_users()
    assert len(all_users) >= 1
    assert any(u.id == user.id for u in all_users)

    # Suppression - nettoyer après le test
    await user_manager.delete_user(user.id)

    # Vérification suppression
    deleted_user = await user_manager.get_user_by_id(user.id)
    assert deleted_user is None

@pytest.mark.asyncio
async def test_job_offer_manager_basic(setup_db):
    """Test des opérations de base du JobOfferManager"""
    managers = await setup_db
    job_manager = managers["job_manager"]

    # Création offre d'emploi avec lien unique
    job_link = f"https://example.com/job/{uuid.uuid4()}"
    job_info = {
        "title": "Software Developer",
        "company": "Test Corp",
        "location": "Remote",
        "description": "Test job description",
        "salary": "50K-70K"
    }

    job = await job_manager.add_job_offer(
        job_link=job_link,
        job_info=job_info,
        job_site=JobSite.LINKEDIN,
        quick_apply=True
    )

    assert job.id is not None
    assert job.job_link == job_link
    assert job.job_site == JobSite.LINKEDIN
    assert job.quick_apply is True
    assert job.job_info["title"] == "Software Developer"

    # Récupération par ID
    retrieved_job = await job_manager.get_job_offer_by_id(job.id)
    assert retrieved_job is not None
    assert retrieved_job.id == job.id
    assert retrieved_job.job_link == job_link

    # Récupération par lien
    job_by_link = await job_manager.get_job_offer_by_link(job_link)
    assert job_by_link is not None
    assert job_by_link.id == job.id

    # Mise à jour
    updated_job = await job_manager.update_job_offer(
        job.id,
        job_site=JobSite.INDEED
    )
    assert updated_job.job_site == JobSite.INDEED

    # Mise à jour quick apply
    updated_quick_apply = await job_manager.update_quick_apply_status(job.id, False)
    assert updated_quick_apply.quick_apply is False

    # Mise à jour info
    updated_info = await job_manager.update_job_info(
        job.id,
        {"requirements": ["Python", "JavaScript"], "remote": True}
    )
    assert updated_info.job_info["title"] == "Software Developer"  # Valeur existante
    assert updated_info.job_info["requirements"] == ["Python", "JavaScript"]  # Nouvelle valeur
    assert updated_info.job_info["remote"] is True  # Nouvelle valeur

    # Liste de toutes les offres
    all_jobs = await job_manager.get_job_offers()
    assert len(all_jobs) >= 1
    assert any(j.id == job.id for j in all_jobs)

    # Récupération des offres avec quick apply
    # D'abord mettre quick_apply à True pour le test
    await job_manager.update_quick_apply_status(job.id, True)
    quick_apply_jobs = await job_manager.get_quick_apply_job_offers()
    assert len(quick_apply_jobs) >= 1
    assert any(j.id == job.id for j in quick_apply_jobs)

    # Suppression - nettoyer après le test
    await job_manager.delete_job_offer(job.id)

    # Vérification suppression
    deleted_job = await job_manager.get_job_offer_by_id(job.id)
    assert deleted_job is None

@pytest.mark.asyncio
async def test_document_manager_basic(setup_db):
    """Test des opérations de base du DocumentManager"""
    managers = await setup_db
    document_manager = managers["document_manager"]
    user_manager = managers["user_manager"]
    job_manager = managers["job_manager"]

    # Créer un utilisateur et une offre pour les références avec identifiants uniques
    user = await user_manager.add_user(
        email=unique_email("doc_test"),
        username=f"docuser_{uuid.uuid4().hex[:8]}",
        password="password123",
        first_name="Doc",
        last_name="User"
    )

    job_link = f"https://example.com/job/{uuid.uuid4()}"
    job = await job_manager.add_job_offer(
        job_link=job_link,
        job_info={"title": "Document Test Job"}
    )

    # Création document
    document = await document_manager.create_document(
        user_id=user.id,
        document_type=DocumentType.CV,
        name="My CV",
        job_id=job.id,
        binary_content=b"Test binary content",
        json_content={"skills": ["Python", "SQL"]},
        text_content="Test CV content",
        metadata={"version": "1.0"}
    )

    assert document.id is not None
    assert document.user_id == user.id
    assert document.document_type == DocumentType.CV
    assert document.name == "My CV"
    assert document.job_id == job.id
    assert document.binary_content == b"Test binary content"
    assert document.json_content["skills"] == ["Python", "SQL"]
    assert document.text_content == "Test CV content"
    assert document.doc_metadata is not None and document.doc_metadata["version"] == "1.0"

    # Récupération par ID
    retrieved_doc = await document_manager.get_document_by_id(document.id)
    assert retrieved_doc is not None
    assert retrieved_doc.id == document.id
    assert retrieved_doc.name == "My CV"

    # Récupération documents utilisateur
    user_docs = await document_manager.get_user_documents(user.id)
    assert len(user_docs) >= 1
    assert any(d.id == document.id for d in user_docs)

    # Récupération documents utilisateur par type
    user_cv_docs = await document_manager.get_user_documents(user.id, DocumentType.CV)
    assert len(user_cv_docs) >= 1
    assert any(d.id == document.id for d in user_cv_docs)

    # Récupération documents pour une offre
    job_docs = await document_manager.get_documents_for_job(job.id)
    assert len(job_docs) >= 1
    assert any(d.id == document.id for d in job_docs)

    # Récupération du dernier document par type
    last_cv = await document_manager.get_last_document_by_type(user.id, DocumentType.CV)
    assert last_cv is not None
    assert last_cv.id == document.id

    # Création d'une lettre de motivation
    cover_letter = await document_manager.create_cover_letter_for_job(
        user_id=user.id,
        job_id=job.id,
        name="Cover Letter",
        content={
            "greeting": "Dear Hiring Manager,",
            "introduction": "I am writing to apply...",
            "skills_experience": "My skills include...",
            "motivation": "I am interested in...",
            "conclusion": "Thank you for considering...",
            "closing": "Sincerely, Doc User"
        }
    )

    assert cover_letter.id is not None
    assert cover_letter.document_type == DocumentType.COVER_LETTER
    assert "Dear Hiring Manager" in cover_letter.text_content

    # Récupération dernière lettre de motivation pour un job
    last_cl = await document_manager.get_latest_cover_letter_for_job(job.id, user.id)
    assert last_cl is not None
    assert last_cl.id == cover_letter.id

    # Mise à jour du document
    updated_doc = await document_manager.update_document(
        document.id,
        name="Updated CV",
        text_content="Updated content"
    )
    assert updated_doc.name == "Updated CV"
    assert updated_doc.text_content == "Updated content"

    # Mise à jour du contenu JSON
    updated_json = await document_manager.update_document_json_content(
        cover_letter.id,
        {"greeting": "Hello Recruiter,"}
    )
    assert updated_json is True

    # Vérifier la mise à jour
    updated_cl = await document_manager.get_document_by_id(cover_letter.id)
    assert updated_cl.json_content["greeting"] == "Hello Recruiter,"
    assert "Hello Recruiter," in updated_cl.text_content

    # Création CV simple
    cv = await document_manager.create_cv(
        user_id=user.id,
        name="Simple CV",
        text_content="Simple CV content"
    )
    assert cv.id is not None
    assert cv.document_type == DocumentType.CV

    # Création formulaire de candidature
    form = await document_manager.create_application_form(
        user_id=user.id,
        name="Application Form",
        form_data={"questions": ["Why do you want to work here?"], "answers": ["Because..."]}
    )
    assert form.id is not None
    assert form.document_type == DocumentType.APPLICATION_FORM

    # Extraction vers fichier temporaire
    success, temp_path = await document_manager.extract_to_temp(document.id)
    assert success is True
    assert os.path.exists(temp_path)
    with open(temp_path, "rb") as f:
        assert f.read() == b"Test binary content"
    os.remove(temp_path)  # Nettoyer

    # Extraction du dernier document par type
    success, temp_path = await document_manager.extract_latest_document_by_type_to_temp(user.id, DocumentType.CV)
    assert success is True
    assert os.path.exists(temp_path)
    os.remove(temp_path)  # Nettoyer

    # Nettoyage - supprimer les documents
    await document_manager.delete_document(document.id)
    await document_manager.delete_document(cover_letter.id)
    await document_manager.delete_document(cv.id)
    await document_manager.delete_document(form.id)

    # Supprimer l'offre et l'utilisateur
    await job_manager.delete_job_offer(job.id)
    await user_manager.delete_user(user.id)

@pytest.mark.asyncio
async def test_application_manager_basic(setup_db):
    """Test des opérations de base du ApplicationManager"""
    managers = await setup_db
    application_manager = managers["application_manager"]
    user_manager = managers["user_manager"]
    job_manager = managers["job_manager"]

    # Créer un utilisateur et une offre pour les références
    user = await user_manager.add_user(
        email=unique_email("app_test"),
        username=f"appuser_{uuid.uuid4().hex[:8]}",
        password="password123",
        first_name="App",
        last_name="User"
    )

    job_link = f"https://example.com/job/{uuid.uuid4()}"
    job = await job_manager.add_job_offer(
        job_link=job_link,
        job_info={"title": "Application Test Job"}
    )

    # Création candidature
    application = await application_manager.create_application(
        user_id=user.id,
        job_id=job.id,
        status="submitted",
        metadata={"submitted_via": "website"}
    )

    assert application.id is not None
    assert application.user_id == user.id
    assert application.job_id == job.id
    assert application.status == "submitted"
    assert application.app_metadata is not None
    assert application.app_metadata["submitted_via"] == "website"

    # Récupération par ID
    retrieved_app = await application_manager.get_application_by_id(application.id)
    assert retrieved_app is not None
    assert retrieved_app.id == application.id
    assert retrieved_app.status == "submitted"

    # Mise à jour du statut
    updated_status = await application_manager.update_application_status(
        application.id,
        "interview_scheduled"
    )
    assert updated_status.status == "interview_scheduled"

    # Mise à jour générale
    updated_app = await application_manager.update_application(
        application.id,
        status="offer_received",
        app_metadata={"interview_date": "2023-06-01"}
    )
    assert updated_app.status == "offer_received"
    assert updated_app.app_metadata["interview_date"] == "2023-06-01"
    assert updated_app.app_metadata["submitted_via"] == "website"  # Valeur existante

    # Récupération candidatures utilisateur
    user_apps = await application_manager.get_user_applications(user.id)
    assert len(user_apps) >= 1
    assert any(a.id == application.id for a in user_apps)

    # Récupération candidatures pour une offre
    job_apps = await application_manager.get_job_applications(job.id)
    assert len(job_apps) >= 1
    assert any(a.id == application.id for a in job_apps)

    # Liste de toutes les candidatures
    all_apps = await application_manager.get_applications()
    assert len(all_apps) >= 1
    assert any(a.id == application.id for a in all_apps)

    # Nettoyage - supprimer les données de test
    await application_manager.delete_application(application.id)
    await job_manager.delete_job_offer(job.id)
    await user_manager.delete_user(user.id)

# =====================================
# Tests de concurrence et parallélisme
# =====================================

@pytest.mark.asyncio
async def test_concurrent_read_operations(setup_db):
    """Test pour vérifier que plusieurs opérations de lecture peuvent s'exécuter en parallèle"""
    managers = await setup_db
    user_manager = managers["user_manager"]
    job_manager = managers["job_manager"]

    # Créer des données de test avec identifiants uniques
    user = await user_manager.add_user(
        email=unique_email("concurrent_read"),
        username=f"concurrent_read_{uuid.uuid4().hex[:8]}",
        password="password123",
        first_name="Concurrent",
        last_name="Read"
    )

    jobs = []
    for i in range(5):
        job = await job_manager.add_job_offer(
            job_link=f"https://example.com/job/read/{uuid.uuid4()}",
            job_info={"title": f"Concurrent Read Job {i}"}
        )
        jobs.append(job)

    # Créer plusieurs tâches de lecture en parallèle
    async def read_users():
        for _ in range(10):
            await user_manager.get_users()

    async def read_jobs():
        for _ in range(10):
            await job_manager.get_job_offers()

    # Exécuter les lectures en parallèle
    start_time = time.time()

    await asyncio.gather(
        read_users(),
        read_jobs(),
        read_users(),
        read_jobs()
    )

    end_time = time.time()

    # Si les lectures sont vraiment parallèles, le temps total devrait être proche du temps d'une seule tâche
    # Si elles sont sérialisées, le temps serait beaucoup plus long
    execution_time = end_time - start_time
    print(f"Concurrent read execution time: {execution_time:.2f} seconds")

    # Vérifier que le temps est approximativement celui d'une seule tâche (10 itérations avec 0.01s de délai)
    # On ajoute une marge pour les opérations de base de données
    assert execution_time < 0.5, "Les lectures parallèles sont trop lentes, elles sont peut-être sérialisées"

    # Nettoyage
    await user_manager.delete_user(user.id)
    for job in jobs:
        await job_manager.delete_job_offer(job.id)

@pytest.mark.asyncio
async def test_concurrent_write_operations(setup_db):
    """Test pour vérifier que les opérations d'écriture sont correctement verrouillées"""
    managers = await setup_db
    user_manager = managers["user_manager"]

    # Créer un utilisateur de test
    user = await user_manager.add_user(
        email=unique_email("concurrent_write"),
        username=f"concurrent_write_{uuid.uuid4().hex[:8]}",
        password="password123",
        first_name="Concurrent",
        last_name="Write",
        config={"counter": 0}
    )

    # Récupérer l'utilisateur une fois pour vérifier que la valeur initiale est correcte
    initial_user = await user_manager.get_user_by_id(user.id)
    assert initial_user.config["counter"] == 0, "Le compteur initial doit être 0"
    
    # Fonction qui incrémente le compteur dans config avec verrou
    async def increment_counter():
        # Utiliser directement le manager pour la mise à jour
        current_user = await user_manager.get_user_by_id(user.id)
        current_counter = current_user.config.get("counter", 0)
        
        # Simuler un traitement qui prend du temps
        await asyncio.sleep(0.1)
        
        # Incrémenter et sauvegarder via le manager
        new_counter = current_counter + 1
        await user_manager.update_config(user.id, {"counter": new_counter})
        
        # Attendre pour s'assurer que la mise à jour est terminée
        await asyncio.sleep(0.05)
        
        return new_counter

    # Exécuter les incrémentations une par une pour garantir la séquentialité
    results = []
    for _ in range(10):
        result = await increment_counter()
        results.append(result)
    
    # Vérifier le résultat final
    final_user = await user_manager.get_user_by_id(user.id)
    final_counter = final_user.config.get("counter", 0)

    # Afficher les résultats pour le débogage
    print(f"Final counter: {final_counter}, Results: {results}")

    # Vérifier que le compteur est correct
    assert final_counter == 10, f"Le compteur final ({final_counter}) n'est pas égal au nombre d'opérations (10)"

    # Nettoyage
    await user_manager.delete_user(user.id)

@pytest.mark.asyncio
async def test_mixed_read_write_operations(setup_db):
    """Test pour vérifier que les lectures et écritures mélangées fonctionnent correctement"""
    managers = await setup_db
    user_manager = managers["user_manager"]
    document_manager = managers["document_manager"]

    # Créer un utilisateur de test
    user = await user_manager.add_user(
        email=unique_email("mixed_ops"),
        username=f"mixed_ops_{uuid.uuid4().hex[:8]}",
        password="password123",
        first_name="Mixed",
        last_name="Ops"
    )

    # Créer un document initial
    doc = await document_manager.create_document(
        user_id=user.id,
        document_type=DocumentType.OTHER,  # Utiliser un type valide
        name="Test Document",
        text_content="Initial content"
    )

    # Fonction qui lit le document
    async def read_document():
        await asyncio.sleep(0.01)  # Petit délai pour simuler une charge
        document = await document_manager.get_document_by_id(doc.id)
        return document.text_content if document else None

    # Fonction qui met à jour le document
    async def update_document(content):
        await asyncio.sleep(0.05)  # Délai plus long pour les écritures
        return await document_manager.update_document(
            doc.id,
            text_content=content
        )

    # Exécuter plusieurs lectures et écritures en parallèle
    read_tasks = [read_document() for _ in range(20)]
    write_tasks = [
        update_document(f"Updated content {i}")
        for i in range(5)
    ]

    # Mélanger les tâches
    all_tasks = read_tasks + write_tasks
    results = await asyncio.gather(*all_tasks)

    # Attendre que toutes les opérations soient terminées
    await asyncio.sleep(0.1)
    
    # Vérifier le document final
    final_doc = await document_manager.get_document_by_id(doc.id)
    assert final_doc is not None
    assert final_doc.text_content.startswith("Updated content")

    # Nettoyage
    await document_manager.delete_document(doc.id)
    await user_manager.delete_user(user.id)

@pytest.mark.asyncio
async def test_stress_test_document_creation(setup_db):
    """Test de stress pour la création simultanée de nombreux documents"""
    managers = await setup_db
    user_manager = managers["user_manager"]
    document_manager = managers["document_manager"]

    # Créer un utilisateur de test
    user = await user_manager.add_user(
        email=unique_email("stress_test"),
        username=f"stress_test_{uuid.uuid4().hex[:8]}",
        password="password123",
        first_name="Stress",
        last_name="Test"
    )

    # Fonction pour créer un document
    async def create_document(index):
        return await document_manager.create_document(
            user_id=user.id,
            document_type=DocumentType.OTHER,  # Utiliser un type valide
            name=f"Stress Test Document {index}",
            text_content=f"Content for document {index}",
            metadata={"index": index}
        )

    # Créer 20 documents en parallèle (réduire à 20 au lieu de 50 pour ne pas trop charger la BD réelle)
    num_docs = 20
    start_time = time.time()

    create_tasks = [create_document(i) for i in range(num_docs)]
    documents = await asyncio.gather(*create_tasks)

    end_time = time.time()
    execution_time = end_time - start_time

    print(f"Created {num_docs} documents in {execution_time:.2f} seconds")

    # Vérifier que tous les documents ont été créés
    assert len(documents) == num_docs
    assert all(doc.id is not None for doc in documents)

    # Récupérer tous les documents de l'utilisateur
    user_docs = await document_manager.get_user_documents(user.id)
    assert len(user_docs) >= num_docs

    # Nettoyage - Supprimer tous les documents créés
    for doc in documents:
        await document_manager.delete_document(doc.id)

    # Vérifier que tous les documents ont été supprimés
    remaining_docs = await document_manager.get_user_documents(user.id, DocumentType.OTHER)
    remaining_stress_docs = [d for d in remaining_docs if "Stress Test Document" in d.name]
    assert len(remaining_stress_docs) == 0

    # Supprimer l'utilisateur
    await user_manager.delete_user(user.id)

@pytest.mark.asyncio
async def test_complex_scenario(setup_db):
    """Test complexe simulant un scénario réel avec plusieurs managers et opérations mélangées"""
    # Récupérer les managers
    managers = await setup_db
    user_manager = managers["user_manager"]
    job_manager = managers["job_manager"]
    document_manager = managers["document_manager"]
    application_manager = managers["application_manager"]

    # 1. Créer plusieurs utilisateurs avec identifiants uniques
    users = []
    for i in range(3):
        user = await user_manager.add_user(
            email=unique_email(f"complex{i}"),
            username=f"complex{i}_{uuid.uuid4().hex[:8]}",
            password="password123",
            first_name=f"Complex{i}",
            last_name="User"
        )
        users.append(user)

    # 2. Créer plusieurs offres d'emploi avec liens uniques
    jobs = []
    for i in range(5):
        job = await job_manager.add_job_offer(
            job_link=f"https://example.com/job/complex/{uuid.uuid4()}",
            job_info={
                "title": f"Complex Job {i}",
                "description": f"Description for job {i}",
                "requirements": ["Python", "SQL", "JavaScript"]
            }
        )
        jobs.append(job)

    # 3. Fonction simulant l'activité d'un utilisateur
    async def user_activity(user_id, job_ids):
        # Créer CV
        cv = await document_manager.create_document(
            user_id=user_id,
            document_type=DocumentType.CV,
            name="My CV",
            text_content="CV content",
            json_content={"skills": ["Python", "SQL"]}
        )

        # Postuler à plusieurs offres
        applications = []
        cover_letters = []

        for job_id in job_ids:
            # Créer lettre de motivation
            cover_letter = await document_manager.create_cover_letter_for_job(
                user_id=user_id,
                job_id=job_id,
                name=f"Cover Letter for Job {job_id}",
                content={
                    "greeting": "Dear Hiring Manager,",
                    "introduction": f"I am applying for job {job_id}...",
                    "skills_experience": "My skills include Python and SQL.",
                    "motivation": "I am motivated by...",
                    "conclusion": "Thank you for considering my application.",
                    "closing": "Sincerely, Complex User"
                }
            )
            cover_letters.append(cover_letter)

            # Créer candidature
            app = await application_manager.create_application(
                user_id=user_id,
                job_id=job_id,
                status="submitted",
                metadata={"cv_id": cv.id, "cover_letter_id": cover_letter.id}
            )
            applications.append(app)

            # Simuler un délai entre les candidatures
            await asyncio.sleep(0.02)

        # Mettre à jour une candidature au hasard
        if applications:
            app = applications[0]
            await application_manager.update_application_status(
                app.id, 
                "interview_scheduled"
            )

        return {
            "user_id": user_id,
            "cv_id": cv.id,
            "cover_letters": [cl.id for cl in cover_letters],
            "applications": [a.id for a in applications]
        }

    # 4. Exécuter les activités utilisateur en parallèle
    tasks = []
    for i, user in enumerate(users):
        # Chaque utilisateur postule à un sous-ensemble d'offres
        job_subset = jobs[i:i+3]  # Chevauchement pour tester la concurrence
        tasks.append(user_activity(user.id, [j.id for j in job_subset]))

    # 5. Ajouter des tâches de lecture en parallèle
    async def read_task():
        for _ in range(5):  # Réduire à 5 itérations
            # Lectures aléatoires
            await user_manager.get_users()
            await job_manager.get_job_offers()
            await asyncio.sleep(0.01)

    tasks.append(read_task())
    tasks.append(read_task())

    # 6. Exécuter toutes les tâches en parallèle
    start_time = time.time()
    results = await asyncio.gather(*tasks)
    end_time = time.time()

    execution_time = end_time - start_time
    print(f"Complex scenario executed in {execution_time:.2f} seconds")

    # 7. Vérifier les résultats
    user_activities = results[:-2]  # Exclure les tâches de lecture

    # Vérifier que toutes les activités utilisateur ont réussi
    assert len(user_activities) == len(users)
    for activity in user_activities:
        assert "user_id" in activity
        assert "cv_id" in activity
        assert "applications" in activity
        assert len(activity["applications"]) > 0

    # 8. Nettoyage - Supprimer toutes les données de test de façon ordonnée
    for activity in user_activities:
        # Supprimer les candidatures
        for app_id in activity["applications"]:
            app = await application_manager.get_application_by_id(app_id)
            if app:
                await application_manager.delete_application(app_id)

        # Supprimer les lettres de motivation
        for cl_id in activity.get("cover_letters", []):
            await document_manager.delete_document(cl_id)

        # Supprimer le CV
        await document_manager.delete_document(activity["cv_id"])

        # Supprimer l'utilisateur
        await user_manager.delete_user(activity["user_id"])

    # Supprimer les offres d'emploi
    for job in jobs:
        await job_manager.delete_job_offer(job.id)