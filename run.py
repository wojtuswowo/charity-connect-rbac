from src import db, create_app
from src.models import Administrator, OrganizationWorker

app = create_app()

if __name__ == '__main__':
    with app.app_context():

        db.create_all()

        if not Administrator.query.filter_by(email='admin1@charity.pl').first():
            print('Creating Admin account')
            admin = Administrator(
                email='admin1@charity.pl',
                first_name='Karol',
                last_name='Sawicki',
                is_approved = True
            )

            admin.set_password('admin123')
            db.session.add(admin)

        if not Administrator.query.filter_by(email='kd@admin.pl').first():
            print('Creating Admin account')
            admin1 = Administrator(
                    email='kd@admin.pl',
                    first_name='admin',
                    last_name='admin',
                    is_approved=True
                )

            admin1.set_password('123')
            db.session.add(admin1)

        if not OrganizationWorker.query.filter_by(email='kd@work.pl').first():
            print('Creating Worker account')
            worker = OrganizationWorker(
                    email='kd@work.pl',
                    first_name='worker',
                    last_name='worker',
                    is_approved=True
            )

            worker.set_password('123')

            db.session.add(worker)
            db.session.commit()
        app.run(debug=True)
