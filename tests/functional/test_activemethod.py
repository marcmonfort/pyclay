import pytest
from model.family import Dog, Family, Person


def test_activemethod_argument_make_persistent(start_client):
    """
    A dataclay object is made persistent when passed as an argument
    to an activemethod of a persistent object
    """
    family = Family()
    person = Person("Marc", 24)
    family.make_persistent()
    assert person.is_registered == False

    family.add(person)
    assert person.is_registered == True
    assert person == family.members[0]


def test_activemethod_persistent_argument(start_client):
    """
    Persistent objects can be sent as activemethod arguments
    """
    family = Family()
    person = Person("Marc", 24)
    family.make_persistent()
    person.make_persistent()
    family.add(person)
    assert person == family.members[0]


def test_activemethod_defined_properties(start_client):
    """
    Object properties defined in class annotations are sychronized between the client and backend
    """
    person = Person("Marc", 24)
    assert person.age == 24

    person.make_persistent()
    person.add_year()
    assert person.age == 25


def test_activemethod_non_defined_properties(start_client):
    """
    Object properties not defined in class annotations are not synchronized between the client and backend
    """
    dog = Dog("Duna", 6)
    assert dog.dog_age == 6 * 7

    dog.make_persistent()
    dog.add_year()
    assert dog.dog_age == 6 * 7  # Age property is not synchronized
    assert dog.get_dog_age() == 7 * 7


def test_activemethod_inner_make_persistent(start_client):
    """
    Objects crated inside an activemethod should be made persistent
    """
    dog = Dog("Duna", 6)
    dog.make_persistent()
    puppy = dog.new_puppy("Rio")
    assert puppy.is_registered == True
    assert puppy == dog.puppies[0]
    assert puppy.name == "Rio"
    assert puppy.age == 0