import pytest

from coqpyt.coq.lsp.structs import *
from coqpyt.coq.exceptions import *
from coqpyt.coq.changes import *

from utility import *


class TestProofValidFile(SetupProofFile):
    def setup_method(self, method):
        self.setup("test_valid.v")

    def test_delete_and_add(self):
        proof_file = self.proof_file
        proof_file.delete_step(6)

        test_proofs = get_test_proofs("tests/proof_file/expected/valid_file.yml", 2)
        test_proofs["proofs"][0]["steps"].pop(1)
        test_proofs["proofs"][0]["steps"][0]["goals"]["version"] = 1
        for i, step in enumerate(test_proofs["proofs"][0]["steps"]):
            if i != 0:
                step["goals"]["position"]["line"] -= 1
            if i != len(test_proofs["proofs"][0]["steps"]) - 1:
                step["goals"]["goals"]["goals"][0]["hyps"] = []
                step["goals"]["goals"]["goals"][0]["ty"] = "∀ n : nat, 0 + n = n"
        check_proof(test_proofs["proofs"][0], proof_file.proofs[0])

        proof_file.add_step(5, "\n      intros n.")

        test_proofs = get_test_proofs("tests/proof_file/expected/valid_file.yml", 3)
        test_proofs["proofs"][0]["steps"][0]["goals"]["version"] = 1
        check_proof(test_proofs["proofs"][0], proof_file.proofs[0])

        # Check if context is changed correctly
        proof_file.add_step(7, "\n      Print minus.")
        step = {
            "text": "\n      Print minus.",
            "goals": {
                "goals": {
                    "goals": [
                        {"hyps": [{"names": ["n"], "ty": "nat"}], "ty": "0 + n = n"}
                    ]
                },
                "position": {"line": 12, "character": 6},
            },
            "context": [
                {
                    "text": "Notation minus := Nat.sub (only parsing).",
                    "type": "NOTATION",
                }
            ],
        }
        add_step_defaults(step, 4)
        test_proofs["proofs"][0]["steps"].insert(3, step)
        for i, step in enumerate(test_proofs["proofs"][0]["steps"][4:]):
            step["goals"]["version"] = 4
            step["goals"]["position"]["line"] += 1
        check_proof(test_proofs["proofs"][0], proof_file.proofs[0])

        # Add step in beginning of proof
        proof_file.add_step(26, "\n    Print plus.")
        assert proof_file.steps[27].text == "\n    Print plus."

        # Add step to end of proof
        proof_file.add_step(31, "\n    Print plus.")
        assert proof_file.steps[32].text == "\n    Print plus."

        # Delete step in beginning of proof
        proof_file.delete_step(27)
        assert proof_file.steps[27].text == "\n      intros n."

        # Delete step in end of proof
        proof_file.delete_step(41)
        assert proof_file.steps[41].text == "\n    Admitted."

    def test_delete_and_add_outside_proof(self):
        # Add outside of proof
        len_steps = len(self.proof_file.steps)
        self.proof_file.add_step(1, "\nPrint plus.")
        assert len_steps + 1 == len(self.proof_file.steps)
        assert self.proof_file.steps[2].text == "\nPrint plus."

        # Delete outside of proof
        self.proof_file.delete_step(2)
        assert len_steps == len(self.proof_file.steps)
        assert self.proof_file.steps[2].text == "\n\nModule Out."

    def test_change_steps(self):
        proof_file = self.proof_file
        proof_file.change_steps(
            [
                CoqDeleteStep(6),
                CoqAddStep("\n      intros n.", 5),
                CoqAddStep("\n      Print minus.", 7),
            ]
        )

        test_proofs = get_test_proofs("tests/proof_file/expected/valid_file.yml", 2)
        step = {
            "text": "\n      Print minus.",
            "goals": {
                "goals": {
                    "goals": [
                        {"hyps": [{"names": ["n"], "ty": "nat"}], "ty": "0 + n = n"}
                    ]
                },
                "position": {"line": 12, "character": 6},
            },
            "context": [
                {
                    "text": "Notation minus := Nat.sub (only parsing).",
                    "type": "NOTATION",
                }
            ],
        }
        add_step_defaults(step, 2)
        test_proofs["proofs"][0]["steps"].insert(3, step)
        for step in test_proofs["proofs"][0]["steps"][4:]:
            step["goals"]["position"]["line"] += 1
        check_proof(test_proofs["proofs"][0], proof_file.proofs[0])

        # Add step in beginning of proof
        proof_file.change_steps([CoqAddStep("\n    Print plus.", 26)])
        assert proof_file.steps[27].text == "\n    Print plus."

        # # Add step to end of proof
        proof_file.change_steps([CoqAddStep("\n    Print plus.", 31)])
        assert proof_file.steps[32].text == "\n    Print plus."

        # # Delete step in beginning of proof
        proof_file.change_steps([CoqDeleteStep(27)])
        assert proof_file.steps[27].text == "\n      intros n."

        # # Delete step in end of proof
        proof_file.change_steps([CoqDeleteStep(41)])
        assert proof_file.steps[41].text == "\n    Admitted."

    def test_change_steps_add_proof(self):
        proofs = len(self.proof_file.proofs)
        steps_taken = self.proof_file.steps_taken
        self.proof_file.change_steps(
            [
                CoqAddStep("\nTheorem change_steps : forall n:nat, 0 + n = n.", 1),
                CoqAddStep("\nProof.", 2),
                CoqAddStep("\nintros n.", 3),
                CoqAddStep("\nreduce_eq.", 4),
                CoqAddStep("\nQed.", 5),
            ]
        )
        assert self.proof_file.steps_taken == steps_taken + 5
        assert len(self.proof_file.proofs) == proofs + 1

    def test_change_steps_delete_proof(self):
        proofs = len(self.proof_file.proofs)
        steps_taken = self.proof_file.steps_taken
        self.proof_file.change_steps([CoqDeleteStep(14) for _ in range(7)])
        assert self.proof_file.steps_taken == steps_taken - 7
        assert len(self.proof_file.proofs) == proofs - 1


class TestAddOpenProof(SetupProofFile):
    def setup_method(self, method):
        self.setup("test_add_open_proof.v")

    def test_change_steps_add_open_proof(self):
        open_proofs = len(self.proof_file.open_proofs)
        proofs = len(self.proof_file.proofs)
        steps_taken = self.proof_file.steps_taken

        self.proof_file.change_steps(
            [
                CoqAddStep("\nTheorem change_steps : forall n:nat, 0 + n = n.", 0),
                CoqAddStep("\nProof.", 1),
                CoqAddStep("\nintros n.", 2),
            ]
        )
        assert self.proof_file.steps_taken == steps_taken + 3
        assert len(self.proof_file.proofs) == proofs
        assert len(self.proof_file.open_proofs) == open_proofs + 1

    def test_add_step_add_open_proofs(self):
        open_proofs = len(self.proof_file.open_proofs)
        self.proof_file.add_step(0, "\nTheorem add_step : forall n:nat, 0 + n = n.")
        self.proof_file.add_step(0, "\nTheorem add_step2 : forall n:nat, 0 + n = n.")
        self.proof_file.add_step(1, "\nTheorem add_step3 : forall n:nat, 0 + n = n.")
        assert len(self.proof_file.open_proofs) == open_proofs + 3
        assert (
            self.proof_file.open_proofs[0].text
            == "Theorem add_step2 : forall n:nat, 0 + n = n."
        )
        assert (
            self.proof_file.open_proofs[1].text
            == "Theorem add_step3 : forall n:nat, 0 + n = n."
        )
        assert (
            self.proof_file.open_proofs[2].text
            == "Theorem add_step : forall n:nat, 0 + n = n."
        )


class TestOpenClosedProof(SetupProofFile):
    def setup_method(self, method):
        self.setup("test_delete_qed.v")

    def test_delete_qed(self):
        open_proofs = len(self.proof_file.open_proofs)
        proofs = len(self.proof_file.proofs)
        self.proof_file.delete_step(9)

        assert proofs - 1 == len(self.proof_file.proofs)
        assert open_proofs + 1 == len(self.proof_file.open_proofs)

        assert (
            self.proof_file.open_proofs[0].text
            == "Theorem delete_qed : forall n:nat, 0 + n = n."
        )
        assert (
            self.proof_file.open_proofs[1].text
            == "Theorem delete_qed2 : forall n:nat, 0 + n = n."
        )
        assert (
            self.proof_file.open_proofs[2].text
            == "Theorem delete_qed3 : forall n:nat, 0 + n = n."
        )

        assert (
            self.proof_file.proofs[0].text
            == "Theorem delete_qed4 : forall n:nat, 0 + n = n."
        )


class TestProofSimpleFileChanges(SetupProofFile):
    def setup_method(self, method):
        self.setup("test_simple_file.v")

    def test_simple_file_changes(self):
        proof_file = self.proof_file
        proof_file.change_steps(
            [
                CoqDeleteStep(1),
                CoqDeleteStep(1),
                CoqDeleteStep(2),
                CoqDeleteStep(2),
                CoqDeleteStep(2),
                CoqAddStep("\nAdmitted.", 0),
                CoqAddStep("\nAdmitted.", 2),
            ]
        )
        assert len(proof_file.steps) == 5
        assert len(proof_file.proofs) == 2

        steps = [
            "Example test1: 1 + 1 = 2.",
            "\nAdmitted.",
            "\n\nExample test2: 1 + 1 + 1= 3.",
            "\nAdmitted.",
        ]
        for i, step in enumerate(steps):
            assert step == proof_file.steps[i].text

        assert proof_file.proofs[0].text == steps[0]
        assert proof_file.proofs[0].steps[0].text == steps[1]
        assert proof_file.proofs[1].text == steps[2].strip()
        assert proof_file.proofs[1].steps[0].text == steps[3]


class TestProofChangeWithNotation(SetupProofFile):
    def setup_method(self, method):
        self.setup("test_change_with_notation.v")

    def test_change_with_notation(self):
        # Just checking if the program does not crash
        self.proof_file.add_step(len(self.proof_file.steps) - 3, " destruct (a <? n).")


class TestProofChangeInvalidFile(SetupProofFile):
    def setup_method(self, method):
        self.setup("test_invalid_1.v")

    def test_change_invalid_file(self):
        with pytest.raises(InvalidFileException):
            self.proof_file.add_step(7, "Print plus.")
        with pytest.raises(InvalidFileException):
            self.proof_file.delete_step(7)
        with pytest.raises(InvalidFileException):
            self.proof_file.change_steps([])


class TestProofInvalidChanges(SetupProofFile):
    def setup_method(self, method):
        self.setup("test_invalid_changes.v")
        self.n_steps = len(self.proof_file.steps)
        self.diagnostics = self.proof_file.diagnostics
        with open(self.proof_file.path, "r") as f:
            self.text = f.read()
        self.goals = []
        for proof in self.proof_file.proofs:
            for step in proof.steps:
                self.goals.append(step.goals)

    def __check_rollback(self, new=0):
        assert self.n_steps == len(self.proof_file.steps)
        assert self.proof_file.is_valid
        assert len(self.proof_file.diagnostics) == len(self.diagnostics) + new
        with open(self.proof_file.path, "r") as f:
            assert self.text == f.read()
        i = 0
        for proof in self.proof_file.proofs:
            for step in proof.steps:
                assert step.goals == self.goals[i]
                i += 1

    def test_invalid_add(self):
        # File becomes invalid
        with pytest.raises(InvalidAddException):
            # Add a non-existing tactic
            self.proof_file.add_step(6, "\n    invalid_tactic.")
        self.__check_rollback(new=1)
        with pytest.raises(InvalidAddException):
            # Add an existing tactic that fails
            self.proof_file.add_step(6, "\n    inversion 1.")
        self.__check_rollback(new=1)
        with pytest.raises(InvalidAddException):
            # Add a tactic when there are no goals
            self.proof_file.add_step(7, "\n    reflexivity.")
        self.__check_rollback(new=1)
        with pytest.raises(InvalidAddException):
            # Add a tactic with undefined tokens
            self.proof_file.add_step(6, "\n    invalid_tactic x $$$ y.")
        self.__check_rollback(new=1)

        # File remains valid but not a valid step
        with pytest.raises(InvalidAddException):
            # Add two valid steps
            self.proof_file.add_step(6, "\n    Check A.x. Check A.x.")
        self.__check_rollback(new=2)
        with pytest.raises(InvalidAddException):
            # Modify the previous step
            self.proof_file.add_step(6, "x.")
        self.__check_rollback()
        with pytest.raises(InvalidAddException):
            # Modify the next step
            self.proof_file.add_step(6, " try")
        self.__check_rollback()
        # TODO: Handle this case. Should this be allowed or not?
        # with pytest.raises(InvalidAddException):
        #     # Modify existing steps and add a new one
        #     self.proof_file.add_step(6, "x. Check A.x. try")
        #     self.__check_rollback()
        with pytest.raises(InvalidAddException):
            # Add whitespaces to end of file
            self.proof_file.add_step(8, "\n \t")
        self.__check_rollback()
        with pytest.raises(InvalidAddException):
            # Add comment to end of file
            self.proof_file.add_step(8, "\n(* I'm useless *)")
        self.__check_rollback()

    def test_invalid_delete(self):
        with pytest.raises(InvalidDeleteException):
            # Delete proof term
            self.proof_file.delete_step(4)
        self.__check_rollback(new=2)
        with pytest.raises(InvalidDeleteException):
            # Delete necessary proof step
            self.proof_file.delete_step(7)
        self.__check_rollback()


class TestProofChangeEmptyProof(SetupProofFile):
    def setup_method(self, method):
        self.setup("test_change_empty.v")

    def test_change_empty_proof(self):
        proof_file = self.proof_file
        assert len(proof_file.proofs) == 0
        assert len(proof_file.open_proofs) == 1

        proof_file.add_step(len(proof_file.steps) - 2, "\nAdmitted.")

        assert len(proof_file.proofs) == 1
        assert len(proof_file.open_proofs) == 0
        assert proof_file.steps[-2].text == "\nAdmitted."
        assert len(proof_file.proofs[0].steps) == 2
        assert proof_file.proofs[0].steps[-1].text == "\nAdmitted."

        proof_file.delete_step(len(proof_file.steps) - 2)
        assert len(proof_file.steps) == 3
        assert len(proof_file.proofs) == 0
        assert len(proof_file.open_proofs) == 1
        assert len(proof_file.open_proofs[0].steps) == 1

        # Delete Proof.
        proof_file.delete_step(1)
        assert len(proof_file.open_proofs[0].steps) == 0

        # Delete Lemma statement
        proof_file.delete_step(0)
        assert len(proof_file.open_proofs) == 0


class TestProofChangeNestedProofs(SetupProofFile):
    def setup_method(self, method):
        self.setup("test_nested_proofs.v")

    def test_change_nested_proofs(self):
        proof_file = self.proof_file
        # Take back last (empty) step
        proof_file.exec(-1)

        # Close proofs in file
        proof_file.add_step(proof_file.steps_taken - 1, "\nQed.")
        proof_file.add_step(proof_file.steps_taken, "\nQed.")
        assert len(proof_file.proofs) == 2
        assert len(proof_file.open_proofs) == 2

        # Close proofs in ProofFile
        proof_file.exec(2)
        assert len(proof_file.proofs) == 4
        assert len(proof_file.open_proofs) == 0

        # Re-open proofs in ProofFile
        proof_file.exec(-2)
        assert len(proof_file.proofs) == 2
        assert len(proof_file.open_proofs) == 2

        # Close proofs in ProofFile again to check rollback
        proof_file.exec(2)
        assert len(proof_file.proofs) == 4
        assert len(proof_file.open_proofs) == 0

        # Re-open proofs in file
        proof_file.exec(-2)
        proof_file.delete_step(proof_file.steps_taken + 1)
        proof_file.delete_step(proof_file.steps_taken)

        # Take last (empty) step
        proof_file.exec(1)
        assert len(proof_file.proofs) == 2
        assert len(proof_file.open_proofs) == 2
        assert proof_file.steps_taken == len(proof_file.steps)
