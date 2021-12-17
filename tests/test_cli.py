import pytest
import sys

def test_argparser(capsys):
  from covert.__main__ import argparse  # Import only *after* capsys wraps sys.stdout/stderr

  # Correct but complex arguments
  sys.argv = "covert enc --recipient recipient1 -r recipient2 -Arrp recipient3 recipient4".split()
  a = argparse()
  assert a.recipients == ['recipient1', 'recipient2', 'recipient3', 'recipient4']
  assert a.paste is True
  assert a.askpass == 1
  # Should produce no output
  cap = capsys.readouterr()
  assert not cap.out
  assert not cap.err

  # Giving mode within combined arguments
  sys.argv = "covert -eArrp recipient1 recipient2".split()
  a = argparse()
  assert a.recipients == ['recipient1', 'recipient2']
  assert a.askpass == 1
  assert a.paste is True
  cap = capsys.readouterr()
  assert not cap.out

  # Missing argument parameter
  sys.argv = "covert enc -Arrp recipient1".split()
  with pytest.raises(SystemExit):
    argparse()
  cap = capsys.readouterr()
  assert not cap.out
  assert "Argument parameter missing: covert enc -Arrp …" in cap.err

  # For combined mode
  sys.argv = "covert -eArrp recipient1".split()
  with pytest.raises(SystemExit):
    argparse()
  cap = capsys.readouterr()
  assert not cap.out
  assert "Argument parameter missing: covert enc -Arrp …" in cap.err


def test_end_to_end(capsys, tmp_path):
  from covert.__main__ import main
  import sys
  fname = tmp_path / "crypto.covert"

  # Encrypt data/foo.txt into crypto.covert
  sys.argv = "covert enc tests/data -R tests/keys/ssh_ed25519.pub -o".split() + [ str(fname) ]
  ret = main()
  cap = capsys.readouterr()
  assert not ret
  assert not cap.out
  assert "foo" in cap.err

  # Decrypt
  sys.argv = "covert dec -i tests/keys/ssh_ed25519".split() + [ str(fname), "-o", str(tmp_path)]
  ret = main()
  cap = capsys.readouterr()
  assert not ret
  assert not cap.out
  assert "foo.txt" in cap.err

  # Check the file just extracted
  with open(tmp_path / "data" / "foo.txt", "rb") as f:
    data = f.read()
  assert data == b"test"


def test_end_to_end_multiple(capsys, tmp_path):
  from covert.__main__ import main
  import sys
  fname = tmp_path / "crypto.covert"

  # Encrypt foo.txt into crypto.covert, with signature
  sys.argv = "covert enc tests/data/foo.txt -i tests/keys/ssh_ed25519 --password verytestysecret -r age1cghwz85tpv2eutkx8vflzjfa9f96wad6d8an45wcs3phzac2qdxq9dqg5p -o".split() + [ str(fname) ]
  ret = main()
  cap = capsys.readouterr()
  assert not ret
  assert not cap.out
  assert "foo" in cap.err

  # Decrypt with key
  sys.argv = "covert dec -i tests/keys/ageid-age1cghwz85tpv2eutkx8vflzjfa9f96wad6d8an45wcs3phzac2qdxq9dqg5p".split() + [ str(fname) ]
  ret = main()
  cap = capsys.readouterr()
  assert not ret
  assert not cap.out
  assert "foo.txt" in cap.err
  assert "Key[827bc3b2:EdPK] Signature verified" in cap.err

  # Decrypt with passphrase
  sys.argv = "covert dec --password verytestysecret".split() + [ str(fname) ]
  ret = main()
  cap = capsys.readouterr()
  assert not ret
  assert not cap.out
  assert "foo.txt" in cap.err
  assert "Key[827bc3b2:EdPK] Signature verified" in cap.err


def test_end_to_end_shortargs_armored(capsys, tmp_path):
  from covert.__main__ import main
  import sys
  fname = tmp_path / "crypto.covert"

  # Encrypt foo.txt into crypto.covert
  sys.argv = "covert -eRao tests/keys/ssh_ed25519.pub".split() + [ str(fname) ] + [ 'tests/data/foo.txt' ]
  ret = main()
  cap = capsys.readouterr()
  assert not ret
  assert not cap.out
  assert "foo" in cap.err

  # Decrypt with key
  sys.argv = "covert -di tests/keys/ssh_ed25519".split() + [ str(fname) ]
  ret = main()
  cap = capsys.readouterr()
  assert not ret
  assert not cap.out
  assert "foo.txt" in cap.err


def test_end_to_end_armormaxsize(capsys, tmp_path):
  from covert.__main__ import main
  import sys
  fname = tmp_path / "test.dat"
  outfname = tmp_path / "crypto.covert"

  # Write 31 MiB on test.dat
  f = open(f"{str(fname)}", "wb")
  f.seek(32505855)
  f.write(b"\0")
  f.close()

  # Encrypt test.dat with armor and padding
  sys.argv = f"covert -e --password verytestysecret --pad 0 -ao".split() + [ str(outfname), str(fname) ]
  ret = main()
  cap = capsys.readouterr()
  assert not ret
  assert not cap.out

  # Decrypt crypto.covert with passphrase
  sys.argv = "covert -d --password verytestysecret".split() + [ str(outfname) ]
  ret = main()
  cap = capsys.readouterr()
  assert not ret
  assert not cap.out



  # Write file with size too large for --armor
  f = open(f"{str(fname)}", "wb")
  f.seek(42505855)
  f.write(b"\0")
  f.close()

  # Try encrypting without -o
  sys.argv = f"covert -ea --password verytestysecret".split() + [ str(fname) ]
  ret = main()
  cap = capsys.readouterr()
  assert not ret
  assert not cap.out
  assert "Too much data for console. How about -o FILE to write a file?" in cap.err

  # Try encrypting with -o
  sys.argv = f"covert -e --password verytestysecret -ao".split() + [ str(outfname), str(fname) ]
  ret = main()
  cap = capsys.readouterr()
  assert not ret
  assert not cap.out
  assert "The data is too large for --armor." in cap.err