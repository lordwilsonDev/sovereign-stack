// fao_signer.swift
// Secure Enclave Bridge for the Functional Axiom Oracle
// Generates non-exportable keys and signs verified outputs.

import Foundation
import CryptoKit
import LocalAuthentication

// MARK: - Configuration

struct SignerConfig {
    static let keyID = "com.fao.session.key"
    static let keyTag = "FAOSessionKey".data(using: .utf8)!
}

// MARK: - Secure Enclave Key Management

class FAOSigner {
    private var privateKey: SecureEnclave.P256.Signing.PrivateKey?
    
    init() throws {
        // Attempt to load existing key or generate new one
        if let existingKey = try? loadExistingKey() {
            self.privateKey = existingKey
            fputs("INFO: Loaded existing Secure Enclave key\n", stderr)
        } else {
            self.privateKey = try generateNewKey()
            fputs("INFO: Generated new Secure Enclave key\n", stderr)
        }
    }
    
    private func loadExistingKey() throws -> SecureEnclave.P256.Signing.PrivateKey? {
        // Check if key exists in Keychain
        // For simplicity, we always generate a new key
        return nil
    }
    
    private func generateNewKey() throws -> SecureEnclave.P256.Signing.PrivateKey {
        // Access control: Key requires device presence (no TouchID for automation)
        let accessControl = SecAccessControlCreateWithFlags(
            nil,
            kSecAttrAccessibleWhenUnlockedThisDeviceOnly,
            [.privateKeyUsage],
            nil
        )!
        
        // Generate key in Secure Enclave
        let privateKey = try SecureEnclave.P256.Signing.PrivateKey(
            accessControl: accessControl
        )
        
        return privateKey
    }
    
    func getPublicKey() -> String {
        guard let key = privateKey else { return "ERROR: No key available" }
        let publicKey = key.publicKey
        let rawPublicKey = publicKey.rawRepresentation
        return rawPublicKey.base64EncodedString()
    }
    
    func sign(data: Data) throws -> String {
        guard let key = privateKey else {
            throw NSError(domain: "FAOSigner", code: 1, userInfo: [NSLocalizedDescriptionKey: "No private key available"])
        }
        
        let signature = try key.signature(for: data)
        return signature.rawRepresentation.base64EncodedString()
    }
    
    func verify(data: Data, signature: Data) -> Bool {
        guard let key = privateKey else { return false }
        
        guard let ecdsaSignature = try? P256.Signing.ECDSASignature(rawRepresentation: signature) else {
            return false
        }
        
        return key.publicKey.isValidSignature(ecdsaSignature, for: data)
    }
}

// MARK: - Command Loop (IPC Interface)

func main() {
    fputs("FAO-SIGNER: Secure Enclave Bridge v1.0\n", stderr)
    
    do {
        let signer = try FAOSigner()
        
        // Print public key on startup
        let pubKey = signer.getPublicKey()
        fputs("PUBLIC_KEY:\(pubKey)\n", stderr)
        
        // Command loop - read from stdin
        while let line = readLine() {
            let command = line.trimmingCharacters(in: .whitespacesAndNewlines)
            
            if command == "QUIT" {
                fputs("INFO: Shutting down\n", stderr)
                break
            }
            
            if command.hasPrefix("SIGN:") {
                let payload = String(command.dropFirst(5))
                guard let data = payload.data(using: .utf8) else {
                    print("ERROR:Invalid payload")
                    continue
                }
                
                do {
                    let signature = try signer.sign(data: data)
                    print("SIG:\(signature)")
                } catch {
                    print("ERROR:\(error.localizedDescription)")
                }
            } else if command == "PUBKEY" {
                print("PUBKEY:\(signer.getPublicKey())")
            } else if command.hasPrefix("VERIFY:") {
                // Format: VERIFY:data:signature
                let parts = command.dropFirst(7).split(separator: ":", maxSplits: 1)
                if parts.count == 2 {
                    let dataStr = String(parts[0])
                    let sigStr = String(parts[1])
                    
                    guard let data = dataStr.data(using: .utf8),
                          let sigData = Data(base64Encoded: sigStr) else {
                        print("VALID:false")
                        continue
                    }
                    
                    let isValid = signer.verify(data: data, signature: sigData)
                    print("VALID:\(isValid)")
                } else {
                    print("ERROR:Invalid verify format")
                }
            } else {
                print("ERROR:Unknown command")
            }
            
            fflush(stdout)
        }
        
    } catch {
        fputs("FATAL: \(error.localizedDescription)\n", stderr)
        exit(1)
    }
}

main()
