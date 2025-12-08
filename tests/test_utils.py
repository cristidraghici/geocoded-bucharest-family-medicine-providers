import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pytest
from utils import extract_street_name_and_number


class TestExtractStreetNameAndNumber:
    """Test suite for address cleanup and extraction."""
    
    def test_strada_abbreviation(self):
        """Test various Strada abbreviations."""
        assert extract_street_name_and_number("Str. Mihai Eminescu, nr 10") == "Strada Mihai Eminescu, 10, Bucuresti"
        assert extract_street_name_and_number("Str Mihai Eminescu, nr 10") == "Strada Mihai Eminescu, 10, Bucuresti"
        assert extract_street_name_and_number("Strada Mihai Eminescu, nr 10") == "Strada Mihai Eminescu, 10, Bucuresti"
    
    def test_bulevardul_abbreviation(self):
        """Test various Bulevardul abbreviations."""
        assert extract_street_name_and_number("Bd. Unirii, nr 5") == "Bulevardul Unirii, 5, Bucuresti"
        assert extract_street_name_and_number("Bld. Unirii, nr 5") == "Bulevardul Unirii, 5, Bucuresti"
        assert extract_street_name_and_number("B-dul Unirii, nr 5") == "Bulevardul Unirii, 5, Bucuresti"
        assert extract_street_name_and_number("Bulevardul Unirii, nr 5") == "Bulevardul Unirii, 5, Bucuresti"
    
    def test_soseaua_abbreviation(self):
        """Test various Soseaua abbreviations."""
        assert extract_street_name_and_number("Sos. Colentina, nr 20") == "Soseaua Colentina, 20, Bucuresti"
        assert extract_street_name_and_number("Soseaua Colentina, nr 20") == "Soseaua Colentina, 20, Bucuresti"
    
    def test_calea_abbreviation(self):
        """Test various Calea abbreviations."""
        assert extract_street_name_and_number("Cal. Victoriei, nr 15") == "Calea Victoriei, 15, Bucuresti"
        assert extract_street_name_and_number("Calea Victoriei, nr 15") == "Calea Victoriei, 15, Bucuresti"
    
    def test_piata_abbreviation(self):
        """Test various Piata abbreviations."""
        assert extract_street_name_and_number("Pta. Unirii, nr 1") == "Piata Unirii, 1, Bucuresti"
        assert extract_street_name_and_number("Piata Unirii, nr 1") == "Piata Unirii, 1, Bucuresti"
    
    def test_aleea_abbreviation(self):
        """Test various Aleea abbreviations."""
        assert extract_street_name_and_number("Al. Parcului, nr 3") == "Aleea Parcului, 3, Bucuresti"
        assert extract_street_name_and_number("Aleea Parcului, nr 3") == "Aleea Parcului, 3, Bucuresti"
    
    def test_intrarea_abbreviation(self):
        """Test various Intrarea abbreviations."""
        assert extract_street_name_and_number("Int. Florilor, nr 2") == "Intrarea Florilor, 2, Bucuresti"
        assert extract_street_name_and_number("Intr. Florilor, nr 2") == "Intrarea Florilor, 2, Bucuresti"
        assert extract_street_name_and_number("Intrarea Florilor, nr 2") == "Intrarea Florilor, 2, Bucuresti"
    
    def test_splaiul_abbreviation(self):
        """Test various Splaiul abbreviations."""
        assert extract_street_name_and_number("Spl. Independentei, nr 7") == "Splaiul Independentei, 7, Bucuresti"
        assert extract_street_name_and_number("Splaiul Independentei, nr 7") == "Splaiul Independentei, 7, Bucuresti"
    
    def test_drumul_abbreviation(self):
        """Test Drumul."""
        assert extract_street_name_and_number("Drumul Taberei, nr 12") == "Drumul Taberei, 12, Bucuresti"
    
    def test_number_variations(self):
        """Test various number format variations."""
        assert extract_street_name_and_number("Str. Test, Nr. 5") == "Strada Test, 5, Bucuresti"
        assert extract_street_name_and_number("Str. Test, Nr 5") == "Strada Test, 5, Bucuresti"
        assert extract_street_name_and_number("Str. Test, Numarul 5") == "Strada Test, 5, Bucuresti"
        assert extract_street_name_and_number("Str. Test, Numarul. 5") == "Strada Test, 5, Bucuresti"
    
    def test_number_not_separated(self):
        """Test number without comma separator."""
        assert extract_street_name_and_number("Str. Testnr 5") == "Strada Test, 5, Bucuresti"
    
    def test_extra_spaces(self):
        """Test handling of extra spaces."""
        assert extract_street_name_and_number("Str.  Test,  nr  5") == "Strada Test, 5, Bucuresti"
        assert extract_street_name_and_number("Str.   Test,   nr   5") == "Strada Test, 5, Bucuresti"
    
    def test_multiple_commas(self):
        """Test handling of multiple commas."""
        assert extract_street_name_and_number("Str. Test,, nr 5") == "Strada Test, 5, Bucuresti"
        assert extract_street_name_and_number("Str. Test,,, nr 5") == "Strada Test, 5, Bucuresti"
    
    def test_unidecode(self):
        """Test Romanian character conversion."""
        assert extract_street_name_and_number("Str. Ștefan cel Mare, nr 10") == "Strada Stefan cel Mare, 10, Bucuresti"
        assert extract_street_name_and_number("Str. Țepeș Vodă, nr 5") == "Strada Tepes Voda, 5, Bucuresti"
    
    def test_complex_address(self):
        """Test complex real-world address."""
        result = extract_street_name_and_number("Bd. Unirii, Numarul 15, Sector 3, Bucuresti")
        assert result == "Bulevardul Unirii, 15, Sector 3, Bucuresti"
    
    def test_sector_full_form(self):
        """Test sector extraction with full form."""
        result = extract_street_name_and_number("Str. Spatar Preda Buzescu Nr. 34, Sector 4")
        assert result == "Strada Spatar Preda Buzescu, 34, Sector 4, Bucuresti"
    
    def test_sector_abbreviation_sect(self):
        """Test sector extraction with 'Sect' abbreviation."""
        result = extract_street_name_and_number("Str. Spatar Preda Buzescu Nr. 34, Sect 4")
        assert result == "Strada Spatar Preda Buzescu, 34, Sector 4, Bucuresti"
    
    def test_sector_abbreviation_sect_dot(self):
        """Test sector extraction with 'Sect.' abbreviation."""
        result = extract_street_name_and_number("Str. Spatar Preda Buzescu Nr. 34, Sect. 4")
        assert result == "Strada Spatar Preda Buzescu, 34, Sector 4, Bucuresti"
    
    def test_no_sector(self):
        """Test address without sector."""
        result = extract_street_name_and_number("Str. Test, nr 5")
        assert result == "Strada Test, 5, Bucuresti"
    
    def test_no_number(self):
        """Test address without number."""
        result = extract_street_name_and_number("Str. Test, Bucuresti")
        assert result == "Strada Test, Bucuresti"
    
    def test_no_street(self):
        """Test address without recognizable street type."""
        result = extract_street_name_and_number("Random Address, nr 5")
        assert result == ", Bucuresti"
    
    def test_case_insensitivity(self):
        """Test case insensitive matching."""
        assert extract_street_name_and_number("str. test, nr 5") == "Strada test, 5, Bucuresti"
        assert extract_street_name_and_number("STR. TEST, NR 5") == "Strada TEST, 5, Bucuresti"
        assert extract_street_name_and_number("Str. Test, Nr 5") == "Strada Test, 5, Bucuresti"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
