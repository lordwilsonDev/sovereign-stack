import jax
import jax.numpy as jnp
from jaxopt import OSQP

def nagumo_safety_filter(u_nom, h_x, grad_h, alpha=0.1):
    """
    Nagumo Safety Filter using Control Barrier Functions (CBF).
    
    u_nom: Nominal token distribution (logits)
    h_x: Current safety value (scalar)
    grad_h: Gradient of safety value w.r.t. logits
    alpha: Safety margin parameter
    """
    
    # Quadratic Program:
    # min || u - u_nom ||^2
    # s.t. grad_h @ (u - u_nom) >= -alpha * h_x
    
    def objective(u):
        return 0.5 * jnp.sum((u - u_nom)**2)
    
    # Constraint: dot(grad_h, u) >= dot(grad_h, u_nom) - alpha * h_x
    # In OSQP form: A u <= b or l <= A u <= u
    # Here: grad_h @ u >= some_lower_bound
    
    lower_bound = jnp.dot(grad_h, u_nom) - alpha * h_x
    
    # Identity matrix for Q, linear term p = -u_nom
    # Resulting x^T Q x + p^T x = 0.5 u^2 - u_nom * u
    
    Q = jnp.eye(len(u_nom))
    p = -u_nom
    
    A = grad_h.reshape(1, -1)
    l = jnp.array([lower_bound])
    u_bound = jnp.array([jnp.inf])
    
    qp = OSQP()
    # Note: jaxopt.OSQP takes (params, Q, p, A, l, u)
    sol = qp.run(None, Q=Q, p=p, A=A, l=l, u=u_bound).params
    
    return sol

if __name__ == "__main__":
    # Test with mock data
    vocab_size = 10
    u_nom = jnp.zeros(vocab_size)
    u_nom = u_nom.at[0].set(10.0)  # Model really wants to pick token 0
    
    # Scenario: Token 0 is unsafe (grad_h points away from it)
    h_x = 0.5  # Current safety is okay
    grad_h = jnp.array([-1.0, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1])
    
    u_safe = nagumo_safety_filter(u_nom, h_x, grad_h)
    
    print(f"Nominal logits: {u_nom}")
    print(f"Safe logits: {u_safe}")
    print(f"Shift in token 0: {u_safe[0] - u_nom[0]:.4f}")
