# Password policy

Policy uses configurable minimum/maximum length and history depth without brittle character-class rules. History retains only salted scrypt hashes and credential metadata. Recent reuse is rejected through safe hash verification.
