import unittest
import time
import numpy as np
from pydl import NoOutputLstm, mathutils


def err(y):
    return np.sum(np.square(y)) / len(y)


def derr(y):
    return (2 / len(y)) * y


def ce_err_prime(y, t):
    return y - t


class TestNoOutputLstm(unittest.TestCase):
    def test_single_step_gradients(self):
        t = 1e-4

        input_size = 4
        hidden_size = 5

        xs = [np.random.uniform(size=input_size)]
        h0 = np.random.uniform(size=hidden_size)

        n = NoOutputLstm(input_size, hidden_size)

        intermediate_results = {}
        h_next = n.forward_prop(xs, h0, intermediate_results)
        dh0 = n.back_prop(derr(h_next), intermediate_results)

        def grad_check(attribute, numerical_gradient):
            for i in np.ndindex(numerical_gradient.shape):
                plus_n = n.clone()
                getattr(plus_n, attribute)[i] += t

                neg_n = n.clone()
                getattr(neg_n, attribute)[i] -= t

                plus_h_next = plus_n.forward_prop(xs, h0, {})
                neg_h_next = neg_n.forward_prop(xs, h0, {})
                exp_grad = (err(plus_h_next) - err(neg_h_next)) / (2 * t)

                self.assertTrue(abs(exp_grad - numerical_gradient[i]) < 0.01,
                                "{}: {} not within threshold of {}".format(attribute, numerical_gradient[i], exp_grad))
        checks = {
            "w_xf_g": intermediate_results["dw_xf_g"],
            "w_hf_g": intermediate_results["dw_hf_g"],
            "b_f_g": intermediate_results["db_f_g"],
            "w_xi_g": intermediate_results["dw_xi_g"],
            "w_hi_g": intermediate_results["dw_hi_g"],
            "b_i_g": intermediate_results["db_i_g"],
            "w_xc": intermediate_results["dw_xc"],
            "w_hc": intermediate_results["dw_hc"],
            "b_c": intermediate_results["db_c"]
        }

        for attr, numerical_grad in list(checks.items()):
            grad_check(attr, numerical_grad)

        for i in np.ndindex(dh0.shape):
            h0_plus = np.copy(h0)
            h0_plus[i] += t

            h0_minus = np.copy(h0)
            h0_minus[i] -= t

            plus_h1 = n.forward_prop(xs, h0_plus, {})
            neg_h1 = n.forward_prop(xs, h0_minus, {})
            exp_dh0 = ((err(plus_h1) - err(neg_h1)) / (2 * t))

            self.assertTrue(abs(exp_dh0 - dh0[i]) < 0.01,
                            "dh_prev: {} not within threshold of {}".format(dh0[i], exp_dh0))

    def test_multi_step_gradients(self):
        t = 1e-4

        x_size = 4
        h_size = 5
        xs = np.random.uniform(size=(10, x_size))
        h0 = np.random.uniform(size=h_size)

        n = NoOutputLstm(x_size, h_size)

        intermediate_results = {}
        h_last = n.forward_prop(xs, h0, intermediate_results)
        dh0 = n.back_prop(derr(h_last), intermediate_results)

        def grad_check(attribute, numerical_gradient):
            for i in np.ndindex(numerical_gradient.shape):
                plus_n = n.clone()
                getattr(plus_n, attribute)[i] += t

                neg_n = n.clone()
                getattr(neg_n, attribute)[i] -= t

                plus_h_last = plus_n.forward_prop(xs, h0, {})
                neg_h_last = neg_n.forward_prop(xs, h0, {})
                exp_grad = (err(plus_h_last) - err(neg_h_last)) / (2 * t)
                num_grad = numerical_gradient[i]

                self.assertTrue(abs(exp_grad - num_grad) < 0.01,
                                "{}: {} not within threshold of {}".format(attribute, numerical_gradient[i], exp_grad))
        checks = {
            "w_xf_g": intermediate_results["dw_xf_g"],
            "w_hf_g": intermediate_results["dw_hf_g"],
            "b_f_g": intermediate_results["db_f_g"],
            "w_xi_g": intermediate_results["dw_xi_g"],
            "w_hi_g": intermediate_results["dw_hi_g"],
            "b_i_g": intermediate_results["db_i_g"],
            "w_xc": intermediate_results["dw_xc"],
            "w_hc": intermediate_results["dw_hc"],
            "b_c": intermediate_results["db_c"]
        }

        for attr, numerical_grad in list(checks.items()):
            grad_check(attr, numerical_grad)

        for i in np.ndindex(dh0.shape):
            plus_h0 = np.copy(h0)
            plus_h0[i] += t

            neg_h0 = np.copy(h0)
            neg_h0[i] -= t

            plus_h_last = n.forward_prop(xs, plus_h0, {})
            neg_h_last = n.forward_prop(xs, neg_h0, {})
            exp_grad = (err(plus_h_last) - err(neg_h_last)) / (2 * t)
            num_grad = dh0[i]

            self.assertTrue(abs(exp_grad - num_grad) < 0.01,
                            "h0: {} not within threshold of {}".format(dh0[i], exp_grad))

    def test_learn_word_vectors_from_char_vector_sequence(self):
        text = "please learn how to infer word vectors from sequences of character vectors"

        index_to_word = list(set(text.split()))
        index_to_char = list(set(text))

        word_to_index = {word: index for index, word in enumerate(index_to_word)}
        char_to_index = {word: index for index, word in enumerate(index_to_char)}

        def to_char_vector_sequence(word):
            sequence = []
            for char in word:
                vector = np.ones(len(char_to_index)) * -1
                vector[char_to_index[char]] = 1
                sequence.append(vector)
            sequence.append(np.zeros(len(char_to_index)))

            return np.asarray(sequence)

        def to_word_vector(word):
            vector = np.ones(len(word_to_index)) * -1
            vector[word_to_index[word]] = 1
            return vector

        training_data = [(to_char_vector_sequence(word), to_word_vector(word)) for word in text.split()]
        n = NoOutputLstm(len(index_to_char), len(index_to_word))

        for i in range(1000):
            for char_vectors, word_vector in training_data:
                intermediate_results = {}
                h_last = n.forward_prop(char_vectors, np.zeros(len(index_to_word)), intermediate_results)
                n.back_prop(ce_err_prime(h_last, word_vector), intermediate_results)
                n.train(0.1, intermediate_results)

            if i % 200 == 0:
                total_err = 0
                for char_vectors, word_vector in training_data:
                    h = n.activate(char_vectors, np.zeros(len(index_to_word)))
                    total_err += mathutils.mean_squared_error(h, word_vector)
                print((total_err/len(training_data)))

        result = n.activate(to_char_vector_sequence("infer"), np.zeros(len(index_to_word)))
        self.assertEquals("infer", index_to_word[np.argmax(result)])

    def test_training_performance(self):
        n = NoOutputLstm(100, 80)
        training_data = []
        for _ in range(30):
            xs = np.asarray([np.random.uniform(size=100),
                             np.random.uniform(size=100),
                             np.random.uniform(size=100),
                             np.random.uniform(size=100),
                             np.random.uniform(size=100),
                             np.random.uniform(size=100),
                             np.random.uniform(size=100),
                             np.random.uniform(size=100)])
            h0 = np.random.uniform(size=80)
            t = np.random.uniform(size=80)
            training_data.append((xs, h0, t))

        epochs = 100
        start = time.time()
        for _ in range(epochs):
            for xs, h0, t in training_data:
                intermediate_results = {}
                h_last = n.forward_prop(xs, h0, intermediate_results)
                n.back_prop(ce_err_prime(h_last, t), intermediate_results)
                n.train(0.1, intermediate_results)
        end = time.time()
        time_taken = end - start

        print((str(epochs) + " training epochs took " + str(time_taken) + " seconds"))

if __name__ == '__main__':
    unittest.main()