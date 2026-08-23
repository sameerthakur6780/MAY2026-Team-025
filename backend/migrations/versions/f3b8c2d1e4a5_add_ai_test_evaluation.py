"""add ai test evaluation fields and tables

Revision ID: f3b8c2d1e4a5
Revises: e2a1f6b0c9d4
Create Date: 2026-08-23 12:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = "f3b8c2d1e4a5"
down_revision = "e2a1f6b0c9d4"
branch_labels = None
depends_on = None


def upgrade():
    # PostgreSQL enum types must be explicitly created before they are used
    # in batch_alter_table/add_column; op.create_table auto-creates them, but
    # batch_alter_table does not.
    # SQLAlchemy's Enum(PyEnumClass) stores the member NAME (uppercase), not
    # its value, matching the convention used by roleenum/submissionstatus/
    # resourcetype elsewhere in this codebase.
    evaluationstatus_enum = postgresql.ENUM(
        "NOT_SCHEDULED",
        "SCHEDULED",
        "RUNNING",
        "COMPLETED",
        "FAILED",
        name="evaluationstatus",
        create_type=True,
    )
    evaluationstatus_enum.create(op.get_bind(), checkfirst=True)

    gradedsource_enum = postgresql.ENUM(
        "MANUAL",
        "AI",
        name="gradedsource",
        create_type=True,
    )
    gradedsource_enum.create(op.get_bind(), checkfirst=True)

    with op.batch_alter_table("tests", schema=None) as batch_op:
        batch_op.add_column(sa.Column("question_paper_resource_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("answer_key_resource_id", sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "evaluation_status",
                sa.Enum(
                    "NOT_SCHEDULED",
                    "SCHEDULED",
                    "RUNNING",
                    "COMPLETED",
                    "FAILED",
                    name="evaluationstatus",
                ),
                nullable=False,
                server_default="NOT_SCHEDULED",
            )
        )
        batch_op.add_column(sa.Column("evaluation_scheduled_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("evaluation_started_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("evaluation_completed_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("evaluation_error", sa.Text(), nullable=True))
        batch_op.create_index("ix_tests_evaluation_status", ["evaluation_status"], unique=False)
        batch_op.create_foreign_key(
            "fk_tests_question_paper_resource_id_resources",
            "resources",
            ["question_paper_resource_id"],
            ["id"],
        )
        batch_op.create_foreign_key(
            "fk_tests_answer_key_resource_id_resources",
            "resources",
            ["answer_key_resource_id"],
            ["id"],
        )

    with op.batch_alter_table("test_submissions", schema=None) as batch_op:
        batch_op.add_column(sa.Column("ai_marks", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("ai_feedback", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("ai_model_used", sa.String(length=200), nullable=True))
        batch_op.add_column(sa.Column("ai_graded_at", sa.DateTime(), nullable=True))
        batch_op.add_column(
            sa.Column(
                "graded_source",
                sa.Enum("MANUAL", "AI", name="gradedsource"),
                nullable=True,
            )
        )

    op.create_table(
        "test_answer_key_questions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("test_id", sa.Integer(), nullable=False),
        sa.Column("question_no", sa.Integer(), nullable=False),
        sa.Column("question_text", sa.Text(), nullable=False),
        sa.Column("expected_answer", sa.Text(), nullable=False),
        sa.Column("max_marks", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["test_id"], ["tests.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("test_id", "question_no", name="uq_test_answer_key_question_no"),
    )
    with op.batch_alter_table("test_answer_key_questions", schema=None) as batch_op:
        batch_op.create_index("ix_test_answer_key_questions_test_id", ["test_id"], unique=False)

    op.create_table(
        "test_question_scores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("submission_id", sa.Integer(), nullable=False),
        sa.Column("answer_key_question_id", sa.Integer(), nullable=False),
        sa.Column("awarded_marks", sa.Integer(), nullable=False),
        sa.Column("feedback", sa.Text(), nullable=True),
        sa.Column("student_excerpt", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["answer_key_question_id"], ["test_answer_key_questions.id"]),
        sa.ForeignKeyConstraint(["submission_id"], ["test_submissions.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "submission_id",
            "answer_key_question_id",
            name="uq_test_question_score_submission_question",
        ),
    )
    with op.batch_alter_table("test_question_scores", schema=None) as batch_op:
        batch_op.create_index("ix_test_question_scores_submission_id", ["submission_id"], unique=False)
        batch_op.create_index(
            "ix_test_question_scores_answer_key_question_id",
            ["answer_key_question_id"],
            unique=False,
        )


def downgrade():
    with op.batch_alter_table("test_question_scores", schema=None) as batch_op:
        batch_op.drop_index("ix_test_question_scores_answer_key_question_id")
        batch_op.drop_index("ix_test_question_scores_submission_id")
    op.drop_table("test_question_scores")

    with op.batch_alter_table("test_answer_key_questions", schema=None) as batch_op:
        batch_op.drop_index("ix_test_answer_key_questions_test_id")
    op.drop_table("test_answer_key_questions")

    with op.batch_alter_table("test_submissions", schema=None) as batch_op:
        batch_op.drop_column("graded_source")
        batch_op.drop_column("ai_graded_at")
        batch_op.drop_column("ai_model_used")
        batch_op.drop_column("ai_feedback")
        batch_op.drop_column("ai_marks")

    with op.batch_alter_table("tests", schema=None) as batch_op:
        batch_op.drop_constraint("fk_tests_answer_key_resource_id_resources", type_="foreignkey")
        batch_op.drop_constraint("fk_tests_question_paper_resource_id_resources", type_="foreignkey")
        batch_op.drop_index("ix_tests_evaluation_status")
        batch_op.drop_column("evaluation_error")
        batch_op.drop_column("evaluation_completed_at")
        batch_op.drop_column("evaluation_started_at")
        batch_op.drop_column("evaluation_scheduled_at")
        batch_op.drop_column("evaluation_status")
        batch_op.drop_column("answer_key_resource_id")
        batch_op.drop_column("question_paper_resource_id")

    # Drop the custom enum types after removing the columns that depend on them.
    postgresql.ENUM(name="gradedsource", create_type=True).drop(op.get_bind(), checkfirst=True)
    postgresql.ENUM(
        name="evaluationstatus", create_type=True
    ).drop(op.get_bind(), checkfirst=True)
